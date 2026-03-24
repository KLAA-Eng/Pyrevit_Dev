
you can add information to the readme (probably shoudl migrate to a notion site eventually and reference that here)

Process for modifying code and comitting it to Git:

Git checkout -b dev

Modify code….

Git add .

Git status

Git commit -m “this is how I modified my code”

Git push origin dev

Open pull request on Github, (SEE DIFF)

Complete pull request w/ comment

Git checkout main

Git pull origin main

Git branch -d dev

Git push origin --delete dev

you can do this from terminal in VSCode (or CodeSpace on Github)