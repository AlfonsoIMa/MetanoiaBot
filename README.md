# MetanoiaBot
A Python Telegram Bot for the Metanoia Ministry, designed to provide information on private chats and keep track of reading/prayer groups the bot is included in.

## Table of Contents
- [Usage](#usage)
- [License](#license)
- [Changelog](#changelog)

## Description
The logic behind the bot sufficees the following ideas:
    - /start will trigger the initiation of the bot on the user/group chat:
        - In individual chats, a the bot asks for a language to communicate and displays various options to provide information about the Metanoia ministry, both in german and ukranian.
        - In group chars, the bot will ask for a language to communicate and, once provided, will ask every member of the chat to talk to it in the group to confim group members and registry on the server database; after that, it'll monitor activity and keep a streak on the daily activity of the chat.

## Usage
To run the project, use the following command:
```bash
npm start
```

## License
This project is licensed under the [MIT License](LICENSE).

## Changelog
#### v1.1.0
- ADDED: Language support in full German and Ukranian.
- FIXED: Texts on private chat fixed to displayed correctly.
- FIXED: Rewritten logic of registration into database.
- 

#### v1.0.0
- ADDED: Bot implementation for the first time (non-documented).
- ADDED: Chat and streak tracking capabilities.
- ADDED: Texts fully in german.
- ADDED: Administrator commands to update bot activities in registered chats.
- ADDED: Administrator commands to broadcast messages across all groups.
