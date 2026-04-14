[Skip to content](https://jkaflik.github.io/OpenMowerNext/contributing.html#VPContent)

On this page

# Contributing [​](https://jkaflik.github.io/OpenMowerNext/contributing.html\#contributing)

## Getting Started [​](https://jkaflik.github.io/OpenMowerNext/contributing.html\#getting-started)

To get started with project development, you should have overall sense of [ROS](https://ros.org/). If you are not familiar with ROS, you can start with [ROS2 tutorials](https://docs.ros.org/en/jazzy/Tutorials.html).

## Setting Up the Development Environment [​](https://jkaflik.github.io/OpenMowerNext/contributing.html\#setting-up-the-development-environment)

1. **Fork the Repository**: Fork the main project repository to your own GitHub account.

bash

```
# Navigate to the project's GitHub page and click the 'Fork' button
```

2. **Clone the Repository**:

bash

```
git clone https://github.com/your_username/OpenMowerNext.git
```

3. **Set Up ROS2**: Ensure you have ROS2 installed and configured on your system.

a. **Devcontainer**: follow [devcontainer guide](https://jkaflik.github.io/OpenMowerNext/devcontainer.html) to setup ROS2 development environment using Devcontainer.



INFO



This section is not complete yet. It will be updated as the project progresses. There is no instruction how to setup ROS2 workspace standalone yet. For a reference, [Dockerfile](https://github.com/jkaflik/OpenMowerNext/blob/main/Dockerfile) can be used.


* * *

## Making Changes [​](https://jkaflik.github.io/OpenMowerNext/contributing.html\#making-changes)

1. **Create a New Branch**:

bash

```
git checkout -b feature/new_feature
```

2. **Code**: Implement your changes, adhering to the project's coding style guidelines.

3. **Test**: Validate your changes locally.

   - Unit Tests
   - Integration Tests
4. **Commit**:

bash

```
git commit -m "Implement new_feature"
```

5. **Push**:

bash

```
git push origin feature/new_feature
```


* * *

## Submitting Contributions [​](https://jkaflik.github.io/OpenMowerNext/contributing.html\#submitting-contributions)

1. **Open a Pull Request (PR)**: Navigate to the original repository and click on "New Pull Request".

2. **Describe Your Changes**: Clearly outline what you've done and why.

3. **Code Review**: Engage in the review process with the maintainers.

4. **Merge**: Once approved, your changes will be merged.