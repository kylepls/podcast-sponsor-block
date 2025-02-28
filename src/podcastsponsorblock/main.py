import json
import logging
import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional, MutableMapping, Sequence

from flask import Flask, request, Response, Request

from .models import ServiceConfig, PodcastConfig
from .views import YoutubeMediaView, YoutubeRSSView, ThumbnailView


def initialize_authorization(
    app: Flask, key: str, allow_query_param_auth: bool
) -> None:
    @app.before_request
    def require_authentication():
        if (
            allow_query_param_auth
            and request.args is not None
            and request.args.get("key") == key
        ):
            return
        request_auth = request.authorization
        if (
            request_auth is None
            or request_auth.type != "basic"
            or request_auth.password != key
        ):
            return Response(
                status=401,
                headers={"WWW-Authenticate": 'Basic realm="podcastsponsorblock"'},
            )


def is_true(value: Optional[str]) -> bool:
    return value is not None and value.casefold() == "true".casefold()


def parse_aliases(source: MutableMapping) -> dict[str, str]:
    aliases = dict()
    prefix = "PODCAST_ALIAS_"
    for key, value in source.items():
        if key.startswith(prefix):
            aliases[key[len(prefix) :].lower()] = value
    return aliases


def parse_comma_seperated_value(hostname_str: Optional[str]) -> Sequence[str]:
    if hostname_str is not None:
        return hostname_str.split(",")
    return tuple()


def parse_podcast_configs(config_path: Path) -> dict[str, PodcastConfig]:
    if not config_path.exists() or not config_path.is_file():
        return dict()
    config = ConfigParser()
    config.read(config_path)
    podcast_configs = dict()
    for section_name in config.sections():
        section_values = config[section_name]
        podcast_configs[section_name] = PodcastConfig(
            id=section_name,
            language=section_values.get("language"),
            description=section_values.get("description"),
            itunes_category=section_values.get("itunes_category"),
            explicit=section_values.getboolean("explicit"),
            itunes_id=section_values.get("itunes_id"),
        )
    return podcast_configs


def populate_service_config(source: MutableMapping) -> ServiceConfig:
    data_path = Path(source["PODCAST_DATA_PATH"]).absolute().resolve()
    try:
        return ServiceConfig(
            youtube_api_key=source.pop("PODCAST_YOUTUBE_API_KEY"),
            auth_key=source.pop("PODCAST_AUTH_KEY", None),
            data_path=data_path,
            allow_query_param_auth=is_true(
                source.get("PODCAST_ALLOW_QUERY_PARAM_AUTH", None)
            ),
            append_auth_param_to_resource_links=is_true(
                source.get("PODCAST_APPEND_AUTH_PARAM_TO_RESOURCE_LINKS", None)
            ),
            aliases=parse_aliases(source),
            categories_to_remove=parse_comma_seperated_value(
                source.get("PODCAST_CATEGORIES_TO_REMOVE", "sponsor")
            ),
            trusted_hosts=parse_comma_seperated_value(
                source.get("PODCAST_TRUSTED_HOSTS", None)
            ),
            podcast_configs=parse_podcast_configs(data_path / "podcasts.ini"),
        )
    except KeyError as exception:
        # noinspection PyUnresolvedReferences
        raise ValueError(f"Missing configuration value: {exception}")


def log_service_config(config: ServiceConfig) -> None:
    logging.info(f"Loaded configuration:")
    logging.info(f"  - Data path: {config.data_path}")
    logging.info(f"  - Trusted hosts: {config.trusted_hosts}")
    logging.info(f"  - Aliases: {config.aliases}")
    logging.info(f"  - Categories to remove: {config.categories_to_remove}")
    logging.info(f"   - Podcast configs: {config.podcast_configs}")
    logging.info(
        f"  - YouTube key: {'(configured)' if config.auth_key is not None else ''}"
    )
    logging.info(
        f"  - Auth key: {'(configured)' if config.auth_key is not None else ''}"
    )
    logging.info(f"  - Allow query parameter auth: {config.allow_query_param_auth}")
    logging.info(
        f"  - Append auth parameter to resource links: {config.append_auth_param_to_resource_links}"
    )


def create_app() -> Flask:
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.DEBUG),
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logging.info("Creating app")
    app = Flask(__name__)
    config = populate_service_config(os.environ)
    if not config.allow_query_param_auth and config.append_auth_param_to_resource_links:
        raise ValueError(
            "Cannot append auth param to resource links when query auth is not allowed"
        )
    log_service_config(config)
    app.config["PODCAST_SERVICE_CONFIG"] = config
    if config.allow_query_param_auth:
        from . import AuthKeyFilteringLogger

        AuthKeyFilteringLogger.enabled = config.allow_query_param_auth
    if config.auth_key is not None:
        initialize_authorization(app, config.auth_key, config.allow_query_param_auth)
    app.request_class.trusted_hosts = list(
        host.removeprefix("http://").removeprefix("https://")
        for host in config.trusted_hosts
    )
    app.add_url_rule(
        "/media/youtube/<string:video_id>",
        view_func=YoutubeMediaView.as_view("youtube_media_view"),
    )
    app.add_url_rule(
        "/rss/youtube/<string:playlist_id>",
        view_func=YoutubeRSSView.as_view("youtube_rss_view"),
    )
    app.add_url_rule(
        "/thumbnail/<string:thumbnail_key>",
        view_func=ThumbnailView.as_view("thumbnail_view"),
    )
    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0")
