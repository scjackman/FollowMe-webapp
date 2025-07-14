# Write GOOGLE_CREDENTIALS to a .json file to be used to config Firebase. This will be run on dyno start
echo ${GOOGLE_CREDENTIALS} > serviceAccountKey.json
