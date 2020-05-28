#    Copyright (C) 2020 Presidenza del Consiglio dei Ministri.
#    Please refer to the AUTHORS file for more information.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <https://www.gnu.org/licenses/>.

from immuni_common.sanic import create_app, run_app
from immuni_exposure_ingestion.apis import ingestion
from immuni_exposure_ingestion.core.managers import managers

sanic_app = create_app(
    api_title="Exposure Ingestion Service",
    api_description="The Exposure Ingestion Service provides an API for the Mobile Client to "
    "upload its TEKs for the previous 14 days, in the case that the user tests positive for "
    "SARS-CoV-2 and decides to share them. "
    "Contextually, the Mobile Client uploads the Epidemiological Infos from the previous 14 days, "
    "if any. "
    "If some Epidemiological Infos are indeed uploaded, the user's Province of Domicile is "
    "uploaded too. "
    "The upload can only take place with an authorised OTP. "
    "The Exposure Ingestion Service is also responsible for periodically generating the TEK Chunks "
    "to be published by the Exposure Reporting Service. "
    "The TEK Chunks are assigned a unique incremental index and are immutable. "
    "They are generated periodically as the Mobile Clients upload new TEKs. "
    "TEK Chunks older than 14 days are automatically deleted from the database by an async "
    "cleanup job. "
    "Province of Domicile and Epidemiological Infos are forwarded to the Analytics Service.",
    blueprints=(ingestion.bp,),
    managers=managers,
)

if __name__ == "__main__":  # pragma: no cover
    run_app(sanic_app)
