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



import datetime
import os
from xml.etree.ElementTree import Element, ElementTree, SubElement

import sickrage
from sickrage.core.common import dateFormat
from sickrage.core.helpers import replace_extension, indent_xml, chmod_as_parent
from sickrage.metadata_providers.mediabrowser import MediaBrowserMetadata
from sickrage.series_providers.exceptions import SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound


class Mede8erMetadata(MediaBrowserMetadata):
    """
    Metadata generation class for Mede8er based on the MediaBrowser.

    The following file structure is used:

    show_root/series.xml                    (show metadata)
    show_root/folder.jpg                    (poster)
    show_root/fanart.jpg                    (fanart)
    show_root/Season ##/folder.jpg          (season thumb)
    show_root/Season ##/filename.ext        (*)
    show_root/Season ##/filename.xml        (episode metadata)
    show_root/Season ##/filename.jpg        (episode thumb)
    """

    def __init__(self,
                 show_metadata=False,
                 episode_metadata=False,
                 fanart=False,
                 poster=False,
                 banner=False,
                 episode_thumbnails=False,
                 season_posters=False,
                 season_banners=False,
                 season_all_poster=False,
                 season_all_banner=False):

        MediaBrowserMetadata.__init__(
            self, show_metadata, episode_metadata, fanart,
            poster, banner, episode_thumbnails, season_posters,
            season_banners, season_all_poster, season_all_banner
        )

        self.name = "Mede8er"

        self.fanart_name = "fanart.jpg"

        # web-ui metadata template
        # self.eg_show_metadata = "series.xml"
        self.eg_episode_metadata = "Season##\\<i>filename</i>.xml"
        self.eg_fanart = "fanart.jpg"
        # self.eg_poster = "folder.jpg"
        # self.eg_banner = "banner.jpg"
        self.eg_episode_thumbnails = "Season##\\<i>filename</i>.jpg"
        # self.eg_season_posters = "Season##\\folder.jpg"
        # self.eg_season_banners = "Season##\\banner.jpg"
        # self.eg_season_all_poster = "<i>not supported</i>"
        # self.eg_season_all_banner = "<i>not supported</i>"

    def get_episode_file_path(self, ep_obj):
        return replace_extension(ep_obj.location, self._ep_nfo_extension)

    @staticmethod
    def get_episode_thumb_path(ep_obj):
        return replace_extension(ep_obj.location, 'jpg')

    def _show_data(self, show_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser-style series.xml
        returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        root_node = Element("details")
        tv_node = SubElement(root_node, "movie")
        tv_node.attrib["isExtra"] = "false"
        tv_node.attrib["isSet"] = "false"
        tv_node.attrib["isTV"] = "true"

        series_provider_language = show_obj.lang or sickrage.app.config.general.series_provider_default_language
        series_info = show_obj.series_provider.get_series_info(show_obj.series_id, language=series_provider_language)
        if not series_info:
            return False

        # check for title and id
        if not (getattr(series_info, 'name', None) and getattr(series_info, 'id', None)):
            sickrage.app.log.info("Incomplete info for "
                                  "show with id " + str(show_obj.series_id) + " on " + show_obj.series_provider.name + ", skipping it")
            return False

        SeriesName = SubElement(tv_node, "title")
        SeriesName.text = series_info['name']

        if getattr(series_info, "genre", None):
            Genres = SubElement(tv_node, "genres")
            for genre in series_info['genre']:
                cur_genre = SubElement(Genres, "Genre")
                cur_genre.text = genre['name'].strip()

        if getattr(series_info, 'firstAired', None):
            FirstAired = SubElement(tv_node, "premiered")
            FirstAired.text = series_info['firstAired']

        if getattr(series_info, "firstAired", None):
            try:
                year_text = str(datetime.datetime.strptime(series_info["firstAired"], dateFormat).year)
                if year_text:
                    year = SubElement(tv_node, "year")
                    year.text = year_text
            except Exception:
                pass

        if getattr(series_info, 'overview', None):
            plot = SubElement(tv_node, "plot")
            plot.text = series_info["overview"]

        if getattr(series_info, 'rating', None):
            try:
                rating = int(float(series_info['rating']) * 10)
            except ValueError:
                rating = 0

            if rating:
                Rating = SubElement(tv_node, "rating")
                Rating.text = str(rating)

        if getattr(series_info, 'status', None):
            Status = SubElement(tv_node, "status")
            Status.text = series_info['status']

        # if getattr(series_info, "contentrating", None):
        #     mpaa = SubElement(tv_node, "mpaa")
        #     mpaa.text = series_info["contentrating"]

        if getattr(series_info, 'imdbId', None):
            imdb_id = SubElement(tv_node, "id")
            imdb_id.attrib["moviedb"] = "imdb"
            imdb_id.text = series_info['imdbId']

        if getattr(series_info, 'id', None):
            series_id = SubElement(tv_node, "series_id")
            series_id.text = str(series_info['id'])

        if getattr(series_info, 'runtime', None):
            Runtime = SubElement(tv_node, "runtime")
            Runtime.text = str(series_info['runtime'])

        cast = SubElement(tv_node, "cast")
        for person in series_info['people']:
            if 'name' not in person or not person['name'].strip():
                continue

            if person['role'].strip() == 'Actor':
                cur_actor = SubElement(cast, "actor")

                cur_actor_role = SubElement(cur_actor, "role")
                cur_actor_role.text = person['role'].strip()

                cur_actor_name = SubElement(cur_actor, "name")
                cur_actor_name.text = person['name'].strip()

                if person['imageUrl'].strip():
                    cur_actor_thumb = SubElement(cur_actor, "thumb")
                    cur_actor_thumb.text = person['imageUrl'].strip()

        indent_xml(root_node)

        data = ElementTree(root_node)

        return data

    def _ep_data(self, ep_obj):
        """
        Creates an elementTree XML structure for a MediaBrowser style episode.xml
        and returns the resulting data object.

        show_obj: a TVShow instance to create the NFO for
        """

        eps_to_write = [ep_obj] + ep_obj.related_episodes

        series_provider_language = ep_obj.show.lang or sickrage.app.config.general.series_provider_default_language
        series_info = ep_obj.show.series_provider.get_series_info(ep_obj.show.series_id, language=series_provider_language)
        if not series_info:
            return False

        rootNode = Element("details")
        movie = SubElement(rootNode, "movie")

        movie.attrib["isExtra"] = "false"
        movie.attrib["isSet"] = "false"
        movie.attrib["isTV"] = "true"

        # write an MediaBrowser XML containing info for all matching episodes
        for curEpToWrite in eps_to_write:
            try:
                series_episode_info = series_info[curEpToWrite.season][curEpToWrite.episode]
            except (SeriesProviderEpisodeNotFound, SeriesProviderSeasonNotFound):
                sickrage.app.log.info(
                    f"Unable to find episode {curEpToWrite.season:d}x{curEpToWrite.episode:d} on {ep_obj.show.series_provider.name}"
                    f"... has it been removed? Should I delete from db?")
                return None

            if curEpToWrite == ep_obj:
                # root (or single) episode

                # default to today's date for specials if firstaired is not set
                if curEpToWrite.season == 0 and not getattr(series_episode_info, 'firstAired', None):
                    series_episode_info['firstAired'] = str(datetime.date.min)

                if not (getattr(series_episode_info, 'name', None) and getattr(series_episode_info, 'firstAired', None)):
                    return None

                episode = movie

                if curEpToWrite.name:
                    EpisodeName = SubElement(episode, "title")
                    EpisodeName.text = curEpToWrite.name

                SeasonNumber = SubElement(episode, "season")
                SeasonNumber.text = str(curEpToWrite.season)

                EpisodeNumber = SubElement(episode, "episode")
                EpisodeNumber.text = str(curEpToWrite.episode)

                if getattr(series_info, "firstAired", None):
                    try:
                        year_text = str(datetime.datetime.strptime(series_info["firstAired"], dateFormat).year)
                        if year_text:
                            year = SubElement(episode, "year")
                            year.text = year_text
                    except:
                        pass

                if getattr(series_info, "overview", None):
                    plot = SubElement(episode, "plot")
                    plot.text = series_info["overview"]

                if curEpToWrite.description:
                    Overview = SubElement(episode, "episodeplot")
                    Overview.text = curEpToWrite.description

                if getattr(series_info, 'contentrating', None):
                    mpaa = SubElement(episode, "mpaa")
                    mpaa.text = series_info["contentrating"]

                if not ep_obj.related_episodes and getattr(series_episode_info, "rating", None):
                    try:
                        rating = int((float(series_episode_info['rating']) * 10))
                    except ValueError:
                        rating = 0

                    if rating:
                        Rating = SubElement(episode, "rating")
                        Rating.text = str(rating)

                cast = SubElement(episode, "cast")
                for person in series_info['people']:
                    if 'name' not in person or not person['name'].strip():
                        continue

                    if person['role'].strip() == 'Actor':
                        cur_actor = SubElement(cast, "actor")
                        cur_actor_role = SubElement(cur_actor, "role")
                        cur_actor_role.text = person['role'].strip()

                        cur_actor_name = SubElement(cur_actor, "name")
                        cur_actor_name.text = person['name'].strip()

                        if person['imageUrl'].strip():
                            cur_actor_thumb = SubElement(cur_actor, "thumb")
                            cur_actor_thumb.text = person['imageUrl'].strip()
                    elif person['role'].strip() == 'Writer':
                        writer = SubElement(episode, "credits")
                        writer.text = series_episode_info['writer'].strip()
                    elif person['role'].strip() == 'Director':
                        director = SubElement(episode, "director")
                        director.text = series_episode_info['director'].strip()
                    elif person['role'].strip() == 'Guest Star':
                        cur_actor = SubElement(cast, "actor")
                        cur_actor_name = SubElement(cur_actor, "name")
                        cur_actor_name.text = person['name'].strip()

            else:
                episode = movie

                # append data from (if any) related episodes
                if curEpToWrite.name:
                    EpisodeName = SubElement(episode, "title")

                    if not EpisodeName.text:
                        EpisodeName.text = curEpToWrite.name
                    else:
                        EpisodeName.text = EpisodeName.text + ", " + curEpToWrite.name

                if curEpToWrite.description:
                    Overview = SubElement(episode, "episodeplot")

                    if not Overview.text:
                        Overview.text = curEpToWrite.description
                    else:
                        Overview.text = Overview.text + "\r" + curEpToWrite.description

        indent_xml(rootNode)
        data = ElementTree(rootNode)

        return data

    def write_show_file(self, show_obj):
        """
        Generates and writes show_obj's metadata under the given path to the
        filename given by get_show_file_path()

        show_obj: TVShow object for which to create the metadata

        path: An absolute or relative path where we should put the file. Note that
                the file name will be the default show_file_name.

        Note that this method expects that _show_data will return an ElementTree
        object. If your _show_data returns data in another format yo'll need to
        override this method.
        """

        data = self._show_data(show_obj)
        if not data:
            return False

        nfo_file_path = self.get_show_file_path(show_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                sickrage.app.log.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                chmod_as_parent(nfo_file_dir)

            sickrage.app.log.debug("Writing show nfo file to " + nfo_file_path)

            nfo_file = open(nfo_file_path, 'wb')

            data.write(nfo_file)
            nfo_file.close()
            chmod_as_parent(nfo_file_path)
        except IOError as e:
            sickrage.app.log.error(
                "Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(e))
            return False

        return True

    def write_ep_file(self, ep_obj):
        """
        Generates and writes ep_obj's metadata under the given path with the
        given filename root. Uses the episode's name with the extension in
        _ep_nfo_extension.

        ep_obj: TVEpisode object for which to create the metadata

        file_name_path: The file name to use for this metadata. Note that the extension
                will be automatically added based on _ep_nfo_extension. This should
                include an absolute path.

        Note that this method expects that _ep_data will return an ElementTree
        object. If your _ep_data returns data in another format yo'll need to
        override this method.
        """

        data = self._ep_data(ep_obj)

        if not data:
            return False

        nfo_file_path = self.get_episode_file_path(ep_obj)
        nfo_file_dir = os.path.dirname(nfo_file_path)

        try:
            if not os.path.isdir(nfo_file_dir):
                sickrage.app.log.debug("Metadata dir didn't exist, creating it at " + nfo_file_dir)
                os.makedirs(nfo_file_dir)
                chmod_as_parent(nfo_file_dir)

            sickrage.app.log.debug("Writing episode nfo file to " + nfo_file_path)

            nfo_file = open(nfo_file_path, 'wb')

            data.write(nfo_file)
            nfo_file.close()
            chmod_as_parent(nfo_file_path)
        except IOError as e:
            sickrage.app.log.warning(
                "Unable to write file to " + nfo_file_path + " - are you sure the folder is writable? {}".format(e))
            return False

        return True
