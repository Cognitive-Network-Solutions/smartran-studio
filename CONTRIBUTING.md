<!-- omit in toc -->
# Contributing to SmartRAN Studio

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 🎉

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

<!-- omit in toc -->
## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Your First Code Contribution](#your-first-code-contribution)
- [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
- [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)


## Code of Conduct

This project and everyone participating in it is governed by the
[SmartRAN Studio Code of Conduct](https://github.com/Cognitive-Network-Solutions/smartran-studio/blob/main/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to .


## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://github.com/Cognitive-Network-Solutions/smartran-studio/tree/main/docs).

Before you ask a question, it is best to search for existing [Issues](https://github.com/Cognitive-Network-Solutions/smartran-studio/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/Cognitive-Network-Solutions/smartran-studio/issues/new).
- Provide as much context as you can about what you're running into.
- Provide project and platform versions (nodejs, npm, etc), depending on what seems relevant.

We will then take care of the issue as soon as possible.


## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project licence.

### Contribution Areas and Boundaries

SmartRAN Studio has a layered architecture:


```
┌─────────────┐
│   Browser   │ ← Access web CLI at localhost:8080
└──────┬──────┘
       │
┌──────▼───────────────────────────────────────┐
│  Frontend (React + Vite)                     │
│  • Terminal-style CLI                        │
│  • Command history & autocomplete            │
│  • Interactive wizards                       │
└──────┬───────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│  Backend (FastAPI)                           │
│  • Command processing                        │
│  • Session management                        │
│  • Configuration save/load                   │
└──┬────────────────────────┬──────────────────┘
   │                        │
   │                  ┌─────▼──────┐
   │                  │  Database  │
   │                  │ (ArangoDB) │
   │                  └────────────┘
   │
┌──▼──────────────────────────────────────────┐
│  Simulation Engine (GPU Container)          │
│  • NVIDIA Sionna RF simulation              │
│  • TensorFlow + CUDA acceleration           │
│  • Multi-cell propagation                   │
│  • RSRP computation                          │
└─────────────────────────────────────────────┘
```


To keep the project maintainable and technically correct, different parts of the system have different contribution expectations.

#### ✅ Areas that do **not** require RAN / Sionna domain expertise

These areas are generally safe to work on without deep telecom knowledge:

- **Frontend (React + Vite)**
  - CLI UI behavior (history, autocomplete, prompts, wizards)
  - Layout, styling, themes, accessibility
  - Adding or improving visualizations and dashboards
  - Error and status messaging in the UI

- **Backend gateway (FastAPI) – non-simulation logic**
  - Request/response handling for the web CLI
  - Session and user context management
  - Configuration save/load behavior
  - Input validation and serialization
  - Logging, metrics, and observability around API usage

- **Documentation & Examples**
  - README improvements
  - Usage guides and tutorials
  - Inline code comments
  - High-level architecture diagrams

These contributions can be submitted directly as PRs. If you're unsure whether something touches core simulation behavior, open an issue first.

#### ⚠️ Changes that **require discussion** with maintainers

The following areas are tightly coupled to SmartRAN Studio’s RF modeling and overall architecture and **must be discussed in an issue before implementation**:

- **Simulation Engine (Sionna / TensorFlow / CUDA)**
  - Changes to RF propagation, RSRP/RSRQ/SINR modeling
  - Adding new channel models, ray-tracing, or propagation schemes
  - Modifications to multi-cell or multi-sector computation logic
  - Adjustments to how simulation state is mapped to UE/network entities

- **Backend ⇄ Simulation API Contract**
  - Introducing, renaming, or removing simulator API commands
  - Changing CLI command behavior or request/response structures
  - Any change that breaks existing workflows or affects reproducibility

- **Database schema and data model (ArangoDB)**
  - SmartRAN Studio depends on ArangoDB for:
    - **Document-based storage** (UE reports, configs, simulation outputs)
    - **Graph-based modeling** (topology, UE-to-cell relations)
  - Changes to core collections, graph edges, or entity relationships require discussion.

Performance improvements, batching fixes, and non-semantic refactors are welcome — but they should include tests or clear evidence that simulation results remain consistent.

#### 🔒 Decisions and elements that are **not open for change** via PR

Some project-level decisions are intentionally not up for community modification:

- **Branding & Naming**
  - *SmartRAN Studio*, *Cognitive Network Solutions (CNS)*, and related logos/names must not be changed or removed.
  - Copyright headers and legal attribution cannot be modified.

- **High-level architecture**
  - The layered design (frontend → FastAPI backend → simulation engine + database) is intentional.
  - Large-scale architectural replacements should begin as a discussion issue, not a PR.

If unsure whether a contribution requires discussion, please open an issue — early communication avoids wasted effort.


### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are using the latest version.
- Determine if your bug is really a bug and not an error on your side e.g. using incompatible environment components/versions (Make sure that you have read the [documentation](https://github.com/Cognitive-Network-Solutions/smartran-studio/tree/main/docs). If you are looking for support, you might want to check [this section](#i-have-a-question)).
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the [bug tracker](https://github.com/Cognitive-Network-Solutions/smartran-studio/issues?q=label%3Abug).
- Also make sure to search the internet (including Stack Overflow) to see if users outside of the GitHub community have discussed the issue.
- Collect information about the bug:
- Stack trace (Traceback)
- OS, Platform and Version (Windows, Linux, macOS, x86, ARM)
- Version of the interpreter, compiler, SDK, runtime environment, package manager, depending on what seems relevant.
- Possibly your input and the output
- Can you reliably reproduce the issue? And can you also reproduce it with older versions?

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

> You must never report security related issues, vulnerabilities or bugs including sensitive information to the issue tracker, or elsewhere in public. Instead sensitive bugs must be sent by email to .
<!-- You may add a PGP key to allow the messages to be sent encrypted as well. -->

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/Cognitive-Network-Solutions/smartran-studio/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the behavior you would expect and the actual behavior.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate the issue on their own. This usually includes your code. For good bug reports you should isolate the problem and create a reduced test case.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will try to reproduce the issue with your provided steps. If there are no reproduction steps or no obvious way to reproduce the issue, the team will ask you for those steps and mark the issue as `needs-repro`. Bugs with the `needs-repro` tag will not be addressed until they are reproduced.
- If the team is able to reproduce the issue, it will be marked `needs-fix`, as well as possibly other tags (such as `critical`), and the issue will be left to be [implemented by someone](#your-first-code-contribution).

<!-- You might want to create an issue template for bugs and errors that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->


### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for SmartRAN Studio, **including completely new features and minor improvements to existing functionality**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### Before Submitting an Enhancement

- Make sure that you are using the latest version.
- Read the [documentation](https://github.com/Cognitive-Network-Solutions/smartran-studio/tree/main/docs) carefully and find out if the functionality is already covered, maybe by an individual configuration.
- Perform a [search](https://github.com/Cognitive-Network-Solutions/smartran-studio/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this feature. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset. If you're just targeting a minority of users, consider writing an add-on/plugin library.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/Cognitive-Network-Solutions/smartran-studio/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why. At this point you can also tell which alternatives do not work for you.
- You may want to **include screenshots or screen recordings** which help you demonstrate the steps or point out the part which the suggestion is related to. You can use [LICEcap](https://www.cockos.com/licecap/) to record GIFs on macOS and Windows, and the built-in [screen recorder in GNOME](https://help.gnome.org/users/gnome-help/stable/screen-shot-record.html.en) or [SimpleScreenRecorder](https://github.com/MaartenBaert/ssr) on Linux. <!-- this should only be included if the project has a GUI -->
- **Explain why this enhancement would be useful** to most SmartRAN Studio users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

<!-- You might want to create an issue template for enhancement suggestions that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->

### Your First Code Contribution
<!-- TODO
include Setup of env, IDE and typical getting started instructions?

-->

### Improving The Documentation
<!-- TODO
Updating, improving and correcting the documentation

-->

## Styleguides
### Commit Messages
<!-- TODO

-->

## Join The Project Team
<!-- TODO -->

<!-- omit in toc -->
## Attribution
This guide is based on the [contributing.md](https://contributing.md/generator)!
