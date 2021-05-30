# Table of contents

- [Contributing instructions](#contributing-instructions)
- [Architecture](#architecture)
  - [Environment](#environment)
  - [Repository structure](#repository-structure)
  	 - [Microservices](#microservices) 
  - [Code style](#code-style)
  - [Testing](#testing)
- [Gitflow](#gitflow)
  - [Feature and fixes](#feature-and-fixes)
  - [Releases](#releases)
- [Commits](#commits)
- [How to contribute](#how-to-contribute)
  - [Issues](#issues)
    - [Creating a new issue](#creating-a-new-issue)
    - [Good first issues](#good-first-issues)
  - [Pull requests](#pull-requests)
    - [Pull request checks](#pull-request-checks)
- [Labels](#labels)

# Contributing instructions
Thank you for considering making a contribution to this repository. In this file, you will find guidelines for contributing efficiently. If you are unsure whether this is the appropriate repository for a particular issue, please review the repository structure of this organisation.

Please do not file an issue to ask a question. You will get faster results by using the resources below.

Before proceeding, please review our [Code of Conduct](./CODE_OF_CONDUCT.md).

# Architecture
This section describes the project's architecture. Please read it thoroughly before contributing to the project.


## Environment
The project has been implemented in [Python 3.8](https://www.python.org/). [Poetry](https://python-poetry.org/) is used for dependency management, allowing for a seamless installation of dependencies.

To set up your development environment, run the following command at the project’s root:

```bash
poetry install
```

## Repository Structure
The root folder contains the following folders:

- **common**. This contains the common logic of Immuni’s backend services. It is a [Git](https://git-scm.com/) repository—*immuni-backend-common*—used here as a Git submodule.
- **docker**. This contains the *docker-compose* configuration to seamlessly run the service, as shown in [Environment](#environment).
- **immuni_exposure_ingestion**. This contains the logic of the specific backend service.
tests. This contains the unit tests.

The *immuni_exposure_ingestion* folder is grouped by concerns. Specifically, as follows:

- **apis**. This contains the Sanic API endpoints, with one file per blueprint.
- **core**. This contains the service-specific configurations and the managers.
- **helpers**. This contains a collection of reusable utility methods.
- **models**. This contains the models (e.g., dataclasses, [marshmallow](https://pypi.org/project/marshmallow/), [mongoengine](https://pypi.org/project/mongoengine/)) used by the backend service.

### Microservices
The backend service logic runs microservices, each one identified by a dedicated file within the *immuni_exposure_ingestion* folder. Specifically, as follows:

- **sanic.py**. This contains the _sanic_app_ object, representing the [Sanic](https://pypi.org/project/sanic/) API microservice.
- **celery.py**. This contains the _celery_app_ object, representing the [Celery](https://pypi.org/project/celery/) distributed task management microservice.

To better understand how to run these microservices, see the dedicated commands in [entrypoint.sh](./entrypoint.sh).


## Code style

A script is provided to maintain consistent security and quality standards using the development tools described in the Technology Description's [Backend Services Technologies](https://github.com/immuni-app/documentation/blob/master/Technology%20Description.md#backend-services-technologies) section. This solution permits keeping the checks' configuration files in the common repository.

```bash
poetry run checks immuni_exposure_ingestion
```

When a new pull request is opened, the CI checks for security, formatting, or linting issues. Please solve any before we can proceed with the review.

## Testing
To preserve functionality after every change, please ensure that all existing test cases pass. You may be required to implement additional test cases, in the event that the existing ones do not ensure maximum coverage after your changes.

```bash
poetry run pytest \
    --cov=immuni_exposure_ingestion \
    --cov-branch \
    --cov-fail-under=97 \
    --ignore=common
```

When a new pull request is opened, the CI assesses whether all test cases pass and whether the maximum coverage is reached. Please solve any failures before we can proceed with the review.

# Gitflow
This repository adopts the [Gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) branch management system.

## Feature and fixes

When contributors wish to implement a new feature or a fix, they should branch from the development branch and open a pull request. Branches should have a meaningful name that adheres to the following convention:
```
<type>/name_of_feature_or_fix
```
The *type* prefix should be one of the following:

- **feature**. Used in the case that the branch implements a new feature.
- **fix**. Used in the case that the branch implements a fix.

Valid branch names are:

- *feature/onboarding*
- *fix/paddings*

Invalid branch names are:

- *feat/onboarding*
- *fix_paddings*

## Releases
When the code is ready for a new release, a new release branch is cut from development. From the [Gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) website:

_Once development has acquired enough features for a release (or a predetermined release date is approaching), you fork a release branch off from development. Creating this branch starts the next release cycle, so no new features can be added after this point—only bug fixes, documentation generation, and other release-oriented tasks should go in this branch._

During this stage, the focus is on preparing the release by fixing issues. It is not possible to add new features to the codebase.

# Commits
Please follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/) naming convention for consistency and to avoid problems with our continuous integration systems. The automatic systems also perform checks and mark as not ready for review any pull request that it determines has not followed the convention.

# How to contribute
When you encounter a bug or an issue with the system represented in this repository, you may choose to let the developers know the nature of the issue.

The Immuni project is composed of different repositories—one for each component or service. If you wish to raise something strictly relevant to this repository (i.e., an Exposure Ingestion Service bug), please read on. However, to raise other issues or to highlight other bugs, please open an issue in the [Documentation repository](https://github.com/immuni-app/immuni-documentation). This lets everyone involved see it, consider it, and participate in the discussion, without slowing down the overall process.

## Issues
Before filing a new issue, please browse the relevant section and use the search functionality to check if it has already been filed by someone else.

- If this issue has previously been filed, please do not create a new one. Instead, add more information to the existing issue, or simply add the :+1: symbol to the first message. This helps the project maintainers to identify issues and prioritise accordingly.
- If the issue has not already been filed, please create a new one.

### Creating a new issue
When creating a new issue, there are three categories:

- Bug report
- Feature request
- General issue

Please ensure that you select the appropriate category for the issue. Each one has a unique template designed to elicit the information required to reproduce and fix the issue. If the issue does not fall under Bug report or Feature request, please select General issue. With a general issue, it is especially important to provide a significant amount of detail, to help the project maintainers and any other collaborators understand the issue clearly.

When an issue is opened, a triage label is automatically assigned. The project maintainers are automatically notified of the issue's creation—they endeavour to address all issues as quickly as possible. When the issue has been triaged, a corresponding label will be assigned. Here is a [list of all the possible labels](#labels).

### Good first issues
If you are interested in contributing to Immuni but are unsure where to start, please search for issues with the _Good first issue_ label. These issues are relatively easy tasks that can help you get familiar with the code.

## Pull requests
After opening an issue, you may want to help the developers further. If the issue has been triaged and if the project maintainers give the green light, you may propose a solution. Doing so is always appreciated. For this, please use the Pull Request tool.

Before proceeding, please ensure that your proposal relates to an issue that has already been reviewed.

The first step in opening a pull request is to fork the project. Please log in to your account, then select Fork in the repository's landing page. This allows you to work on a dedicated fork and push your changes there. Then, if you wish to apply these changes back in the main Immuni repository, create a pull request targeting this repository. For more detailed information, [please read this guide](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request-from-a-fork).

When creating a pull request, please choose a name that adheres to the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.2/) naming convention. It is important to review and follow this convention before creating a pull request. This ensures that the commit history remains clean and makes it easy to identify what each commit does.

After choosing the appropriate name, please use the following template for the body of the pull request:

```markdown
<!--- IMPORTANT: Please review [how to contribute](../CONTRIBUTING.md) before proceeding further. -->
<!--- IMPORTANT: If this is a Work in Progress PR, please mark it as such in GitHub. -->

## Description

<!--- Describe in detail the proposed mods -->

This PR tackles:

- ...
- ...
- ...

In particular, the ...

## Checklist

<!--- Please insert an 'x' after you complete each step -->

- [ ] I have followed the indications in the [CONTRIBUTING](../CONTRIBUTING.md).
- [ ] The documentation related to the proposed change has been updated accordingly (plus comments in code).
- [ ] I have written new tests for my core changes, as applicable.
- [ ] I have successfully run tests with my changes locally.
- [ ] It is ready for review! :rocket:

## Fixes

<!-- Please insert the issue numbers after the # symbol -->

- Fixes #ISSUE_NUMBER
```

There is a checklist indicating the different steps to follow. After completing each step, please mark it as such by inserting an X between the [ ]. When all the steps have been completed, the review process begins.

### Pull request checks
When a new pull request is opened, the CI performs some checks. These are as follows:

- Verification that the commits respect the repository's convention
- Verification that the source code is properly formatted
- Verification that the source code is properly linted
- Verification that the test cases are all successful
- Verification that the maximum code converge is reached

Pull requests that fall foul of these rules are not reviewed.

## Labels
Labels are used to tag issues and make them more easily discoverable. Please refer to the [Github website](https://guides.github.com/features/issues/?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) for more information.

| Name             | Description                                                                   |
| ---------------- | ----------------------------------------------------------------------------  |
| bug              | Indicates an unexpected problem or unintended behaviour                       |
| documentation    | Indicates that improvements or additions to the documentation are needed      |
| duplicate        | Indicates similar issues or pull requests                                     |
| enhancement      | Indicates new feature requests                                                |
| good first issue | Indicates a good issue for first-time contributors                            |
| help wanted      | Indicates that a project maintainer wants help on an issue or a pull request  |
| invalid          | Indicates that an issue or a pull request is no longer relevant               |
| question         | Indicates that an issue or a pull request needs more information              |
| wontfix          | Indicates that work won't continue on an issue or a pull request              |
| triage           | Indicates that the issue still needs to be triaged                            |
| QA               | Label coming directly from the QA department                                  |

