# https://github.com/casey/just

vbin   := "./venv/bin"
pip    := vbin / "pip"
python := vbin / "python"

last_commit_sha1   := `git rev-parse --short HEAD`
remote_image_name  := "gitea.gdemontauzan.fr/maxenceg2m/github-release-notifier"
remote_build_image := remote_image_name + ":" + last_commit_sha1

# Run the script
run: init
    {{ python }} notifier.py

# Init python virtual env
init:
    python3 -m venv venv
    {{ pip }} install --requirement requirements.txt

# Clean workspace - remove venv - and init
reinit: hclean init

# Remove virtual env (venv)
hclean:
    rm -fr venv

# Run docker compose then show logs
dup: dbuild
    docker compose up -d
    docker compose logs

# Build with docker compose
dbuild:
    docker compose build

# Down docker compose then build
drebuild: ddown dbuild

# Down docker compose
ddown:
    docker compose down

# Docker build without cache
dforce-build:
    docker compose build --no-cache

# Push a working images on registry, tagged with commit-sha1
dpush: dbuild
    docker tag github-release-notifier {{ remote_build_image }}
    docker push {{ remote_build_image }}
    echo "To push a tagged version, do 'just release <version>'"

# Release a version: create a tagged images, push it and create a git tag
release version: dbuild
    docker tag github-release-notifier {{ remote_image_name }}:{{ version }}
    docker push {{ remote_image_name }}:{{ version }}
    git tag -a v{{ version }} -m ""
