# ##############################################################################
#  Author: echel0n <echel0n@sickrage.ca>
#  URL: https://sickrage.ca/
#  Git: https://git.sickrage.ca/SiCKRAGE/sickrage.git
#  -
#  This file is part of SiCKRAGE.
#  -
#  SiCKRAGE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  -
#  SiCKRAGE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  -
#  You should have received a copy of the GNU General Public License
#  along with SiCKRAGE.  If not, see <http://www.gnu.org/licenses/>.
# ##############################################################################
from marshmallow import fields

from sickrage.core.webserver.handlers.api.schemas import BaseSchema, BaseSuccessSchema


class SeriesSlugPath(BaseSchema):
    """Series slug schema"""

    series_slug = fields.String(
        required=True,
        default=False,
        description="Series slug for series you want to lookup",
    )


class EpisodeSlugPath(BaseSchema):
    """Episode slug schema"""

    episode_slug = fields.String(
        required=True,
        default=False,
        description="Episode slug for episode you want to lookup",
    )


class SeriesEpisodesRenameSuccessSchema(BaseSuccessSchema):
    pass


class SeriesEpisodesManualSearchPath(BaseSchema):
    """Complete episode manual search schema"""

    episode_slug = fields.String(
        required=True,
        default=False,
        description="Episode slug for episode you want to manually search for",
    )


class SeriesEpisodesManualSearchSchema(BaseSchema):
    """Complete episode manual search schema"""

    useExistingQuality = fields.Boolean(
        required=False,
        default=False,
        description="Use existing quality of previous manual episode search",
    )


class SeriesEpisodesManualSearchSuccessSchema(BaseSuccessSchema):
    pass
