import os
import requests
import logging
import typer
import traceback
from typing import List

from job_cd.core.interfaces import ContactFinderStrategy, CacheStrategy
from job_cd.core.models import Company, Contact, DeploymentProfile


class ApolloFinder(ContactFinderStrategy):
    """
    Uses the Apollo.io REST API to find recruiter contacts based on
    the company and your target job titles.
    """
    def __init__(self, cache: CacheStrategy):
        self.api_key = os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY not found in environment variables.")

        self.base_url = 'https://api.apollo.io/api/v1'
        self.people_api_search_endpoint = f'{self.base_url}/mixed_people/api_search'
        self.bulk_people_enrichment_endpoint = f'{self.base_url}/people/bulk_match'
        self.cache = cache

    def find_contacts(self, company: Company, profile: DeploymentProfile) -> List[Contact]:
        logging.info(f"Hunting for contacts at {company.domain} using Apollo...")
        typer.secho(f"🕵️‍♂️  Scouting Apollo for people at {company.domain}...", fg=typer.colors.CYAN)

        try:
            # --- STEP 1: Search for people ---
            params = {
                'person_titles[]': profile.target_contact_titles,
                'include_similar_titles': 'true',
                'q_organization_domains_list[]': [company.domain],
                'contact_email_status[]': ['verified', 'likely to engage'],
                'page': 1,
                'per_page': 5,
            }
            headers = {
                'X-Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            # Prepare the request to log the full URL
            search_response = requests.post(self.people_api_search_endpoint, params=params, headers=headers)
            search_response.raise_for_status()
            search_data = search_response.json()

            people_search_results = search_data.get('people', [])

            if not people_search_results:
                logging.warning(f"No contacts found at {company.domain}.")
                typer.secho(f"🤷‍♂️  No exact matches found at {company.domain}. Moving on!", fg=typer.colors.YELLOW)
                return []

            logging.info(f"Found {len(people_search_results)} potential matches. Enriching data...")
            typer.secho(f"✨  Found {len(people_search_results)} prospects! Digging up their emails...", fg=typer.colors.MAGENTA)


            # --- STEP 2: Prepare data for bulk enrichment ---
            contacts = []
            people_to_enrich = []
            for person in people_search_results:
                if len(people_to_enrich) == 5: # prevents sending more than 5 people tp enrichment api
                    break

                cached_data = self.cache.get(person['id'])
                if cached_data:
                    contacts.append(Contact(**cached_data))
                else:
                    people_to_enrich.append(person)

            # --- STEP 3: Call bulk enrichment API ---
            if len(people_to_enrich) > 0:
                enrichment_payload = {'details': people_to_enrich}
                enrichment_params = {
                    'reveal_personal_emails': 'false',
                    'reveal_phone_number': 'false'
                }

                enrichment_response = requests.post(
                    self.bulk_people_enrichment_endpoint,
                    json=enrichment_payload,
                    headers=headers,
                    params=enrichment_params
                )
                enrichment_response.raise_for_status()
                enrichment_data = enrichment_response.json()

                # --- STEP 4: Map enrichment results into Contact ---
                enriched_people = enrichment_data.get('matches', [])


                for person in enriched_people:
                    # Filter out anyone who still doesn't have an email after enrichment
                    if not person.get('email'):
                        continue

                    contact = Contact(
                        id=person.get('id'),
                        first_name=person.get('first_name'),
                        last_name=person.get('last_name'),
                        name=person.get('name'),
                        email=person.get('email'),
                        phone=person.get('phone'),
                        linkedin=person.get('linkedin_url'),
                        company=company,
                        title=person.get('title'),
                        headline=person.get('headline'),
                        email_status=person.get('email_status'),
                        seniority=person.get('seniority'),
                        departments=person.get('departments', [])
                    )
                    contacts.append(contact)

                    # Persist the contact using the configured CacheStrategy
                    self.cache.set(contact.id, contact.model_dump())

            logging.info(f"Successfully enriched {len(contacts)} actionable contacts!")

            if contacts:
                typer.secho(f"🎯  Success! Locked in {len(contacts)} verified contacts.", fg=typer.colors.GREEN, bold=True)
            else:
                typer.secho("🕵️‍♂️ Found people, but Apollo couldn't verify any emails. Skipping...",
                            fg=typer.colors.YELLOW)

            return contacts

        except requests.exceptions.RequestException as e:
            logging.error(f"Apollo API network request failed: {e}")
            typer.secho(f"🚨  Network hiccup reaching Apollo.io: {e}", fg=typer.colors.RED)
            return []
        except Exception as e:
            logging.exception(f"Unexpected error processing Apollo data: {e}")
            typer.secho(f"💥  Whoops! Something broke while parsing Apollo data: {e}", fg=typer.colors.RED)
            typer.secho(traceback.format_exc(), fg=typer.colors.RED)
            return []
