.. Images
.. |chat_1| image:: images/chat_1.jpg
.. |chat_2| image:: images/chat_2.jpg
.. |chat_3| image:: images/chat_3.jpg
.. |chat_4| image:: images/chat_4.jpg
.. |chat_5| image:: images/chat_5.jpg
.. |chat_6| image:: images/chat_6.jpg

.. Links
.. |chat| raw:: html

   <a href="https://chat.google.com" target="_blank">Google Chat</a>

Google Chat
===========

The *foglamp-notify-google-hangouts* plugin allows notifications to be delivered to the Google chat platform. The notification are delivered into a specific chat room within the application, in order to allow access to the chat room you must create a webhook for sending data to that chatroom.

To create a webhook

  - Go to the |chat| page in your browser

    +----------+
    | |chat_1| |
    +----------+

  - Select the chat room you wish to use or create a new chat room

  - In the menu at the top of the screen select *Configure webhooks*

    +----------+
    | |chat_2| |
    +----------+

  - Enter a name for your webhook and optional avatar and click *Save*

    +----------+
    | |chat_3| |
    +----------+

  - Copy the URL that appears under your webhook name, you can use the copy icon next to the URL to place it in the clipboard

    +----------+
    | |chat_6| |
    +----------+

  - Close the webhooks window by clicking outside the window

Once you have created your notification rule and move on to the delivery mechanism

  - Select the Hangouts plugin from the list of plugins

  - Click *Next*

    +----------+
    | |chat_4| |
    +----------+

  - Now configure the asset delivery plugin

    - **Google Hangout Webhook URL**: Paste the URL obtain above here

    - **Message Text**: Enter the message text you wish to send

  - Enable the plugin and click *Next*

  - Complete your notification setup

A message will be sent to this chat room whenever a notification is triggered.

+----------+
| |chat_5| |
+----------+
