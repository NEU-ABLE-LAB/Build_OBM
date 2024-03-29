<!-- Add banner here -->
![Banner](imgs/occ_banner.png?raw=true "Title")

# Build OBM: Building Occupant Behavior Model

<!-- Reference: https://github.com/navendu-pottekkat/awesome-readme-->
<!-- Describe your project in brief -->
Simulates occupant behavior in a home by integrating 4 seperate model in the agent based modeling environment:
1. **Occupancy model**
2. **Comfort model**
3. **Habitual model (Routine based)**
4. **Discomfort model**

# Demo
<!-- Add a demo for your project -->
## Conda - [**Cheatsheet**](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)
### Environment
`environment.yml` file is available to build the virtual conda environment. The following code in the terminal can be used to create the environment from the file.

> *Note: Modify the last line in the `environment.yml` file to change the directory of the environment*

`conda env create -f environment.yml`

## Input data
In order to run the demo/example simulation, the following input files are required:

1. **ecobee's DyD data**: `sample_data1_stp_processed.h5` file is available in the `input_data` folder. Using an open loop system, model uses indoor and outdoor environment data to simulate overrides.
2. **Occupancy transition matrix**: `transition_matrix.csv` is required to simulate an occupant's presence in an home using a 1st order markov chain model.
3. **Habitual transition matrix**: `TM_habitual.csv` is required to simulation an occupant's habitual routine based override using a 1st order markov chain model.
4. **Classification model**: `model_classification.pkl` is required to simulate the classification of discomfort based overrides per timestep.
5. **Regression model**: `model_regressor.pkl` is required to simulate the time to override once the classification model classifies an override for a timestep.

## Running the demo/example

**&rarr; `example.ipynb`**: The notebook can be run in the [virtual environment](#Environment) created above. This is a demo of an occupant overriding controls for a day using an open-loop system.

A successful simulation run should display a graphic similar to the one below. In this graphic, the spikes depict overrides. As an open-loop system is being used to simulate the indoor environment, the change in setpoint is followed by the changing the setpoint back to the value previous to the override.

![Spikes are overrides](imgs/override_example.png "Simulation run example")


# Table of contents

<!-- After you have introduced your project, it is a good idea to add a **Table of contents** or **TOC** as **cool** people say it. This would make it easier for people to navigate through your README and find exactly what they are looking for.

Here is a sample TOC(*wow! such cool!*) that is actually the TOC for this README.

- [Project Title](#project-title)
- [Demo-Preview](#demo-preview)
- [Table of contents](#table-of-contents)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Contribute](#contribute)
    - [Sponsor](#sponsor)
    - [Adding new features or fixing bugs](#adding-new-features-or-fixing-bugs)
- [License](#license)
- [Footer](#footer)

# Installation
[(Back to top)](#table-of-contents)

*You might have noticed the **Back to top** button(if not, please notice, it's right there!). This is a good idea because it makes your README **easy to navigate.*** 

The first one should be how to install(how to generally use your project or set-up for editing in their machine).

This should give the users a concrete idea with instructions on how they can use your project repo with all the steps.

Following this steps, **they should be able to run this in their device.**

A method I use is after completing the README, I go through the instructions from scratch and check if it is working.

Here is a sample instruction:

To use this project, first clone the repo on your device using the command below:

```git init```

```git clone https://github.com/navendu-pottekkat/nsfw-filter.git```

# Usage
[(Back to top)](#table-of-contents)

This is optional and it is used to give the user info on how to use the project after installation. This could be added in the Installation section also.

# Development
[(Back to top)](#table-of-contents)

This is the place where you give instructions to developers on how to modify the code.

You could give **instructions in depth** of **how the code works** and how everything is put together.

You could also give specific instructions to how they can setup their development environment.

Ideally, you should keep the README simple. If you need to add more complex explanations, use a wiki. Check out [this wiki](https://github.com/navendu-pottekkat/nsfw-filter/wiki) for inspiration.

# Contribute
[(Back to top)](#table-of-contents)

This is where you can let people know how they can **contribute** to your project. Some of the ways are given below.

Also this shows how you can add subsections within a section.

### Sponsor
[(Back to top)](#table-of-contents)

Your project is gaining traction and it is being used by thousands of people(***with this README there will be even more***). Now it would be a good time to look for people or organisations to sponsor your project. This could be because you are not generating any revenue from your project and you require money for keeping the project alive.

You could add how people can sponsor your project in this section. Add your patreon or GitHub sponsor link here for easy access.

A good idea is to also display the sponsors with their organisation logos or badges to show them your love!(*Someday I will get a sponsor and I can show my love*)

### Adding new features or fixing bugs
[(Back to top)](#table-of-contents)

This is to give people an idea how they can raise issues or feature requests in your projects. 

You could also give guidelines for submitting and issue or a pull request to your project.

Personally and by standard, you should use a [issue template](https://github.com/navendu-pottekkat/nsfw-filter/blob/master/ISSUE_TEMPLATE.md) and a [pull request template](https://github.com/navendu-pottekkat/nsfw-filter/blob/master/PULL_REQ_TEMPLATE.md)(click for examples) so that when a user opens a new issue they could easily format it as per your project guidelines.

You could also add contact details for people to get in touch with you regarding your project.

# License
[(Back to top)](#table-of-contents)

Adding the license to README is a good practice so that people can easily refer to it.

Make sure you have added a LICENSE file in your project folder. **Shortcut:** Click add new file in your root of your repo in GitHub -> Set file name to LICENSE -> GitHub shows LICENSE templates -> Choose the one that best suits your project!

I personally add the name of the license and provide a link to it like below.

[GNU General Public License version 3](https://opensource.org/licenses/GPL-3.0)

# Footer
[(Back to top)](#table-of-contents)

Let's also add a footer because I love footers and also you **can** use this to convey important info.

Let's make it an image because by now you have realised that multimedia in images == cool(*please notice the subtle programming joke).

So that is it... You have completed your training young grasshopper. Now it is time for you to use this ideas for your projects.

Don't forget your **README Sensei**(*cool twitter handle idea*) when your project takes off with your **Awesome README**.

Leave a star in GitHub, give a clap in Medium and share this guide if you found this helpful.

**Now folks, the moment you've all been waiting for! The footer!**
***[Audible gasp]***

<!-- Add the footer here ->

![Footer](https://github.com/navendu-pottekkat/awesome-readme/blob/master/fooooooter.png) -->
