## Followme! 

'Followme!' is a simple feed type web-app for following other users. No unfollowing allowed!

This app allows users to create an 'account' by accepting a cookie that holds their public userID. They can sign up with their name and location, and then follow other users in a user feed.

# Stack

This app utilises a HTML/JS frontend with a Flask backend communicating with a Firestore db.

# Setup and Usage

To deploy this app to Heroku, you must have a project set up within Firebase with Firestore enabled. This will act as the database for the project. 

You must provide a config var within the Heroku environment named 'GOOGLE_CREDENTIALS' which should contain your 'serviceAccountKey.json' as a single string. An example format is provided in 'serviceAccountKey.json.example'. This will be echoed to a .json file on startup of the Heroku dyno using the command contatined within '.profile'.

This app may also be run locally using Flask local hosting. This requires having the 'serviceAccountKey.json' file saved within your working directory.

# Future

This app is provided as an example full stack web app only.

