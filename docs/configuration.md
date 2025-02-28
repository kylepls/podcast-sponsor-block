# Configuration

Information on how to configure podcast-sponsor-block can be found below. Please read all sections as some podcast apps
require special configuration.

### Configuring the service
podcast-sponsor-block is configured primarily via environment variables. A list of the available environment variables
is below:

| Name                                        | Description                                                                                                                                                                                                                                                                                                                                                                                                                                    | Required | Default Value |
|---------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------------|
| PODCAST_YOUTUBE_API_KEY                     | A [YouTube API key](https://developers.google.com/youtube/v3/getting-started) used to communicate with the YouTube API                                                                                                                                                                                                                                                                                                                         | Yes      |               |
| PODCAST_DATA_PATH                           | The directory to store data in                                                                                                                                                                                                                                                                                                                                                                                                                 | Yes      |               |
| PODCAST_CATEGORIES_TO_REMOVE                | A comma-seperated list of [SponsorBlock categories](https://github.com/yt-dlp/yt-dlp#sponsorblock-options) to remove when downloading audio                                                                                                                                                                                                                                                                                                    | No       | sponsor       |
| PODCAST_ALIAS_\<alias\>                     | Allows the configuration of aliases to make referencing playlists easier (example: `PODCAST_ALIAS_SCOOTS=PLMdYRoC0mZlW2uoesMXUrac26lsvOupSx` would allow you to reference the playlist `PLMdYRoC0mZlW2uoesMXUrac26lsvOupSx` with the name `scoots` instead)                                                                                                                                                                                    | No       |               |
| PODCAST_AUTH_KEY                            | Enables HTTP basic authentication on the server. `PODCAST_AUTH_KEY` will be used as the password (the username is ignored)                                                                                                                                                                                                                                                                                                                     | No       |               |
| PODCAST_ALLOW_QUERY_PARAM_AUTH              | Allows `PODCAST_AUTH_KEY` to be provided as the query parameter `key`. Please note providing sensitive info as part of the query string [is bad practice](https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url), so only enable this option if your podcast app does not support HTTP basic authentication. When enabled, podcast-sponsor-block will do its best to redact the key from its logs. | No       | false         |
| PODCAST_APPEND_AUTH_PARAM_TO_RESOURCE_LINKS | Causes the feed generator to include `key=<PODCAST_AUTH_KEY>` in resource links. This can only be enabled if `PODCAST_ALLOW_QUERY_PARAM_AUTH` is enabled, and is intended to be used only when it is required to workaround a lack of authentication support in your podcast app.                                                                                                                                                              | No       | false         |
| PODCAST_TRUSTED_HOSTS                       | A comma-seperated list of trusted `Host` header values that can be used to access podcast-sponsor-block (e.g. `http://192.168.1.43:8081,https://podcasts.ericmedina024.com`). If configured, the `Host` header will be used to create absolute URLs. If not configured, relative URLs will be used instead which can cause issues with some podcast apps.                                                                                      | No       |               |
| PODCAST_SPONSORBLOCK_API                    | The SponsorBlock API to use, defaults to https://sponsor.ajay.app                                                                                                                                                                                                                                                                                                                                                                              |          |               |

### Configuring your podcasts

Some podcast apps like Apple Podcasts require specifying additional attributes not available in the YouTube API. To use
podcast-sponsor-block with these services, you will need to create a file called `podcasts.ini` within `PODCAST_DATA_PATH`.
Within `podcasts.ini`, you can configure your podcasts like so (using the Sleep With Me podcast as an example):
```ini
# The name of the section is the YouTube playlist ID (not an alias)
[PLMdYRoC0mZlW2uoesMXUrac26lsvOupSx]
# the two-letter iso 639-1 language code. a list can be found here:
# https://www.loc.gov/standards/iso639-2/php/code_list.php
language=en

# the iTunes ID of the podcast. this can be derived from the podcast url:
# https://podcasts.apple.com/us/podcast/sleep-with-me/id740675898
# the id is the numerical portion at the end of the url
# Apple has very specific requirements for podcast thumbnails, so podcast-sponsor-block
# will use this ID to grab a compliant thumbnail straight from iTunes
itunes_id=740675898

# the iTunes category this podcast fits in. there is a list of valid categories here:
# https://podcasters.apple.com/support/1691-apple-podcasts-categories
# please note: the category name IS case sensitive
itunes_category=Leisure

# If configured, this will override the YouTube playlist description
description=Good night!

# denotes whether this podcast contains explicit content (either yes or no)
explicit=no
```
Please note that some podcast apps (like Apple Podcasts) require **all** of these options to be set. If you are having
trouble with your podcast app not reading the RSS feed correctly, ensure you have set **all** these options for your
podcast.


### Custom thumbnails
Unfortunately, the YouTube API does not provide access to the cover image of podcasts. Due to this,
podcast-sponsor-block will use the channel's avatar as the podcast thumbnail by default. This is often different
from the usual cover image for the podcast.

If you don't like the thumbnail podcast-sponsor-block grabs, you can provide
a custom thumbnail by creating a `thumbnails` directory in `PODCAST_DATA_PATH`. Once created, put your desired
thumbnail image in a file with the same name as the YouTube playlist ID the thumbnail is for (file extensions are
ignored). You can also use your configured aliases as the file name. For example, if you had the alias
`PODCAST_ALIAS_SCOOTS=PLMdYRoC0mZlW2uoesMXUrac26lsvOupSx` configured, then you could name the thumbnail image 
`scoots.<extension>` or `PLMdYRoC0mZlW2uoesMXUrac26lsvOupSx.<extension>`.
