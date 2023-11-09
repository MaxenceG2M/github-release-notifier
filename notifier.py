import datetime
import json
import os
import smtplib
from configparser import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

SMTP_PORT = 0
SMTP_SERVER = "null"
SENDER_EMAIL = "a@b.c"
RECEIVER_EMAIL = "d@e.f"


def main():
    global SMTP_PORT, SMTP_SERVER, SENDER_EMAIL, RECEIVER_EMAIL

    script_dir = os.path.dirname(__file__)
    conf_file = os.path.join(script_dir, "conf.ini")
    template_file = os.path.join(script_dir, "template.html")

    parser = ConfigParser()
    parser.read(conf_file)

    SMTP_PORT = parser.get("config", "smtp_port")
    SMTP_SERVER = parser.get("config", "smtp_server")
    SENDER_EMAIL = parser.get("config", "sender_email")
    RECEIVER_EMAIL = parser.get("config", "receiver_email")

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

    send_mail(template.replace("{{content}}", content))

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


def send_mail(content):
    message = MIMEMultipart("alternative")
    message["Subject"] = "New Github releases"
    message["From"] = SENDER_EMAIL
    message["To"] = RECEIVER_EMAIL

    # part1 = MIMEText(text, "plain")
    part2 = MIMEText(content, "html")

    # message.attach(part1)
    message.attach(part2)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())


def convert_date(date: str, dest_format="%d %b %Y at %H:%M") -> str:
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime(dest_format)


if __name__ == "__main__":
    main()
