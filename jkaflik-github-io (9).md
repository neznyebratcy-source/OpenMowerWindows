[Skip to content](https://jkaflik.github.io/OpenMowerNext/devcontainer.html#VPContent)

On this page

# Devcontainer [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#devcontainer)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#overview)

Devcontainer is a recommended way to setup development environment for this project. It is a Docker container with all the required tools and dependencies.

With a seamless integration with VSCode, it provides a consistent development environment for all developers.

For CLion users there is an alternative approach described in [CLion development environment](https://jkaflik.github.io/OpenMowerNext/clion-env.html).

## Prerequisites [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#prerequisites)

- [Docker](https://docs.docker.com/get-docker/)
- [VSCode](https://code.visualstudio.com/download) or any other IDE/workspace that supports [Devcontainer](https://code.visualstudio.com/docs/remote/containers)
- [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension for VSCode

## Getting Started with VSCode [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#getting-started-with-vscode)

1. **Open repository in VSCode**.
2. **Reopen in Container**. (VSCode should ask for it automatically, but if not, you can do it manually)
   - Click on the green icon in the bottom left corner of the VSCode window.
   - Select `Reopen in Container`.
   - Wait for the container to build.
   - VSCode will reopen in the container.
3. **Enjoy your development environment.**

## Getting Started with [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#getting-started-with)

## Detailed [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#detailed)

Devcontainer comes up with some containers configured with Docker Compose:

- `workspace` \- main container with all the tools and dependencies and mounted workspace
- `xserver` \- container with X server and VNC server for GUI applications
- `groot` \- container with groot, a GUI for [BehaviourTree.CPP](https://www.behaviortree.dev/). It does not start by default. See [GRoot](https://jkaflik.github.io/OpenMowerNext/groot.html) for more details.

All containers share the same X server socket, so GUI applications can be run from the `workspace` container and displayed in the `xserver` container. VNC server in `xserver` runs a web server on port `12345` with a VNC client. You can access it by opening [`http://localhost:12345`](http://localhost:12345/) in your browser.

## Default environment variables loaded in the image [​](https://jkaflik.github.io/OpenMowerNext/devcontainer.html\#default-environment-variables-loaded-in-the-image)

bash

```
#!/usr/bin/env bash

override_env_file=/opt/ws/.devcontainer/override/.env

# Values below are defaults. You can override them by creating a file in .devcontainer/override/.env
# File will be sourced here.

if [ -f "$override_env_file" ]; then
    echo "Sourcing override environment file: $override_env_file"
    source "$override_env_file"
else
    echo "No override environment file found at: $override_env_file"
    echo "Using default values."

    source /opt/ws/.devcontainer/default.env
fi

echo "Map file is expected in $OM_MAP_PATH - $OM_DATUM_LAT, $OM_DATUM_LONG"
```

For more details about the environment variables, see [Configuration](https://jkaflik.github.io/OpenMowerNext/configuration.html).