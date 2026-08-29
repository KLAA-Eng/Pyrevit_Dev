
you can add information to the readme (probably shoudl migrate to a notion site eventually and reference that here)

## Reference Links

- [Python Script Guide](SCRIPTS.md) - KLCode code organization and pyRevit script structure
- [Comment and Docstring Guide](COMMENTS.md) - comments, docstrings, command metadata, and section dividers
- [pyRevit Labs Notion](https://pyrevitlabs.notion.site/)
- [Revit API Docs](https://www.revitapidocs.com/)
- [RVTDocs](https://rvtdocs.com/) - searchable Revit API reference with version comparisons and Python examples
- [Lucide Icons](https://lucide.dev/icons/) — icon-design reference

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
