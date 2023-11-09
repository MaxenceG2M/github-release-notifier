import configparser
import datetime
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests


class EnvInjection(configparser.Interpolation):
    """
    Derived interpolation to take env variable before file variable.
    Permit to keep the ini file for local / traditionnal use
    And use env variable to overload configuration in a Docker usage.
    """

    def before_get(self, parser, section, option, value, defaults):
        file_value = super().before_get(parser, section, option, value, defaults)
        if section != parser.default_section:
            return file_value

        env_value = os.getenv(option.upper())
        return env_value if env_value else file_value


def main():
    script_dir = os.path.dirname(__file__)
    conf_file = os.path.join(script_dir, "conf.ini")
    template_file = os.path.join(script_dir, "template.html")

    parser = configparser.ConfigParser(
        default_section="config", interpolation=EnvInjection()
    )
    parser.read(conf_file)
    default_config = parser["config"]

    projects = json.loads(parser.get("projects", "projects"))
    new_releases = []
    new_projects = []

    if not parser.has_section("release"):
        parser.add_section("release")

    for project in projects:
        last_release = get_last_release(project)

        if not parser.has_option("release", project):
            new_projects.append(last_release)
        else:
            last_config_tag = parser.get("release", project)
            if last_config_tag != last_release["release_tag"]:
                last_release["previous_tag"] = last_config_tag
                new_releases.append(last_release)
        parser.set("release", project, last_release["release_tag"])

    if not new_releases and not new_projects:
        print("No new projets or new release detected. Bye!")
        return

    content = ""

    for new_r in new_releases:
        content += f"""
        <li><a href="{new_r["release_url"]}" target="_blank">{new_r["project_name"]}</a>
        : new release
        <a href="{new_r["release_url"]}" target="_blank">{new_r["release_tag"]}</a>
        available (old: {new_r["previous_tag"]}).
        (published {convert_date(new_r["published_date"])})</li>"""

    for new_p in new_projects:
        content += f"""
        <li><a href="{new_p["release_url"]}" target="_blank">{new_p["project_name"]}</a>
        was added to your configuration.
        Last release:
        <a href="{new_p["release_url"]}" target="_blank">{new_p["release_tag"]}</a>
        (published {convert_date(new_p["published_date"])})</li>"""

    with open(template_file, "r", encoding="utf-8") as f_template:
        template = f_template.read()

    send_mail(template.replace("{{content}}", content), default_config)

    with open("conf.ini", "w", encoding="utf-8") as configfile:
        parser.write(configfile)


def get_last_release(project):
    url = f"https://api.github.com/repos/{project}/releases/latest"
    result = requests.get(url, timeout=10)

    print(project)
    print(url)
    release = result.json()
    release_tag = release["tag_name"]
    published_date = release["published_at"]
    # body = release['body']
    release_url = release["html_url"]

    return {
        "release_tag": release_tag,
        "published_date": published_date,
        # 'body': body,
        "project_name": project,
        "release_url": release_url,
    }


def send_mail(content, config):
    smtp_port = config.get("smtp_port")
    smtp_server = config.get("smtp_server")
    sender_email = config.get("sender_email")
    receiver_email = config.get("receiver_email")

    message = MIMEMultipart("alternative")
    message["Subject"] = "New Github releases"
    message["From"] = sender_email
    message["To"] = receiver_email

    # part1 = MIMEText(text, "plain")
    part2 = MIMEText(content, "html")

    # message.attach(part1)
    message.attach(part2)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.sendmail(sender_email, receiver_email, message.as_string())


def convert_date(date: str, dest_format="%d %b %Y at %H:%M") -> str:
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime(dest_format)


if __name__ == "__main__":
    main()
