# MyCorsiDemoApp

A Corsi block-tapping task implemented in Kivy, designed for the iPad (tested on iPad 9th Generation), and packaged via kivy-ios for deployment using Xcode.

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
3. [File Structure](#file-structure)  
4. [Requirements](#requirements)  
5. [Installation & Build Steps](#installation--build-steps)  
   - [1. Install Homebrew Dependencies](#1-install-homebrew-dependencies)  
   - [2. Clone the kivy-ios Repository](#2-clone-the-kivy-ios-repository)  
   - [3. Create & Activate a Fresh Python Virtual Environment](#3-create--activate-a-fresh-python-virtual-environment)  
   - [4. Install kivy-ios from Source](#4-install-kivy-ios-from-source)  
   - [5. Build Kivy, Python, and Other Libraries](#5-build-kivy-python-and-other-libraries)  
   - [6. Create an iOS Project](#6-create-an-ios-project)  
   - [7. Update Xcode Project Settings](#7-update-xcode-project-settings)  
   - [8. Run/Deploy on an iPad](#8-rundeploy-on-an-ipad)  
6. [Troubleshooting](#troubleshooting)  
7. [About the Corsi Task](#about-the-corsi-task)

---

## Overview

**MyCorsiDemoApp** implements the classic Corsi block-tapping task. Participants see nine blue blocks on the screen. A sequence of blocks lights up in red, one after another. The participant must then tap the blocks:

- **Forward mode:** in the same order they were lit.
- **Backward mode:** in the reverse order.

Sequences start short and get progressively longer until the participant fails twice at a given length. Data (such as reaction times and correct/incorrect sequences) is saved to a CSV file on the iPad’s local storage so that it can be retrieved later (via the Files app, iTunes File Sharing, or other means).

This repository contains:
- `main.py`, `my.kv`, `datahandler.py` (the core Kivy code)
- Example icons (`corsi_icon.png`), fonts, and an example `AppIcon.appiconset`
- Instructions for using kivy-ios to package this into an iOS app

---

## Features

- **Practice Mode:** A small set of practice trials with feedback (Correct / Try again).
- **Forward and Backward Task:** Automatically transitions from forward sequence to backward sequence after completion.
- **Data Saving:** Saves CSV files to the device storage for easy retrieval.
- **iPad-Friendly UI:** Font sizes and layouts adapt for iPad screens.
- **Cleanly Styled:** Custom coloring for blocks, popups, and buttons.

---

## File Structure

A typical folder layout for this project:

<pre lang="markdown">
MyCorsiDemoApp/
├── main.py
├── my.kv
├── datahandler.py
├── fonts/
│   └── (custom fonts, e.g., helvetica.ttf, fontello.ttf)
├── AppIcon.appiconset/
│   └── (... your icon images in various iOS-required resolutions ...)
├── corsi_icon.png
└── README.md
</pre>

## Requirements

- macOS with the latest Xcode (for iOS development)
- Homebrew (for installing dependencies)
- Python 3.8+ (confirmed working with Python 3.8, 3.9, 3.10—some versions may require additional tweaks)
- kivy-ios toolchain (tested at time of writing with kivy-ios main branch)

---

## Installation & Build Steps

Below is an outline of steps to install and build this project onto an iPad:

### 1. Install Homebrew Dependencies

```bash
brew install autoconf automake libtool pkg-config
brew link libtool
```
### 2. Clone the kivy-ios Repository

```bash
cd ~
git clone https://github.com/kivy/kivy-ios.git
cd kivy-ios
```
(If you had a previous kivy-ios folder you want to replace, remove it first.)

### 3. Create & Activate a Fresh Python Virtual Environment
Inside kivy-ios (or anywhere you prefer):

```bash
python3 -m venv venv
source venv/bin/activate
```
### 4. Install kivy-ios from Source
Upgrade pip and install:

```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```
### 5. Build Kivy, Python, and Other Libraries
Build Python:

```bash
toolchain build python3
```

Build Kivy:

```bash
toolchain build kivy
```

Build additional libraries (e.g. plyer for iOS file handling):

```bash
toolchain build plyer
```
(If you see errors about missing Cython, do pip install cython and re-run.)

### 6. Create an iOS Project
Create a new iOS project from the local directory containing your app (MyCorsiDemoApp). In the examples below, we call it CorsiApp:

```bash
toolchain create CorsiApp /path/to/MyCorsiDemoApp
```

This should create a new folder corsiapp-ios (or similarly named) inside kivy-ios. Open that folder in Xcode:

```bash
cd ~/kivy-ios/corsiapp-ios
open CorsiApp.xcodeproj
```

Move or the AppIcon.appiconset folder inside corsiapp/Images.xcassets/ to use custom icons.
Also ensure that corsi_icon.png is added to the Xcode project’s resources if needed for the launch screen.

### 7. Update Xcode Project Settings
#### Info.plist
To allow the CSV output to appear in the Files app on your iPad, add these keys:

```
<key>UIFileSharingEnabled</key>
<true/>
<key>LSSupportsOpeningDocumentsInPlace</key>
<true/>
<key>UISupportsDocumentBrowser</key>
<true/>
```

#### Rename / Display Name
In Xcode, open Info.plist or the target’s Info tab.
Change:
```
Bundle display name   String   $(PRODUCT_NAME)
```
to:

```bash
Bundle display name   String   Corsi
```

#### App Icons
• In the “General” tab of your Xcode target, find App Icons and Launch Images.

•	Select your newly added “AppIcon” asset in App Icons Source.

#### Launch Screen
•	Add an image view referencing corsi_icon.png, or customize the storyboard as needed.

### 8. Run/Deploy on an iPad
•	Connect your iPad to your Mac.

•	In Xcode, choose your iPad device from the scheme dropdown.

•	Build & Run.

You may be prompted for code signing credentials or to create a free developer account if you have not set that up previously.

Once installed on the iPad, open the app. To retrieve the generated CSV data:

•	Open Files on the iPad

•	Under On My iPad → Corsi (or your app name)
 
•	Or use iTunes / Finder (on macOS) file sharing to copy out the .csv files.

---

### Troubleshooting

#### make Issues
If you have a conflicting make in your PATH, you can override it to ensure that /usr/bin/make is used. For example:

```bash
# Example fix to remove a conflicting directory from PATH
export PATH="$(echo $PATH | sed 's|/some/conflicting/folder/bin:||g')"

# Re-insert /usr/bin and your venv/bin in front:
export PATH="$VIRTUAL_ENV/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:$(echo $PATH | sed "s|$VIRTUAL_ENV/bin:||")"
```

Adjust those paths as needed. The point is to ensure that Apple’s native /usr/bin/make is visible first in your PATH.

#### Missing Cython
If you get errors about missing Cython, install it inside your venv:

```bash
pip install cython
```

#### Xcode Code-Signing

You might need an Apple Developer account (paid or free) to deploy onto a physical iPad. In Xcode:

•	Under Signing & Capabilities → Team: select your account.
 
•	Under Bundle Identifier: set a unique identifier (e.g., com.myname.corsi).

#### Graphics / GL Errors
Ensure you’ve built the matching versions of kivy, python3, and other dependencies under the same kivy-ios environment.

## About the Corsi Task

The Corsi block-tapping task is a common measure in cognitive psychology used to assess spatial working memory.

•	Nine blocks are arranged in a fixed layout.

•	Blocks flash one by one in a pseudo-random sequence.

•	The participant must reproduce the sequence by tapping the same blocks (Forward mode) or in reverse (Backward mode).

•	Sequences start short (e.g., 2 blocks) and increase in length until the participant fails twice at a given length.

•	Maximum span is often used as an indicator of spatial working memory capacity.

In this app:

•	Practice sequences help a participant understand the task flow.

•	Data is saved to .csv with time-stamped files.

---









