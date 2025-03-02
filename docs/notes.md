
## ERD
If there is ever the need to regenerate the ERD of the database this is possible with:

This involves django-extensions, see the documentation for more info https://django-extensions.readthedocs.io/en/latest/graph_models.html
`pip install django-extensions`
`pip install pygraphviz` or `pip install pyparsing pydot`

It also requires adding django-extensions as installed application.
As there are no other uses of the extension, it is not left in the final build to reduce weight.

The following example makes use of pydot and manually excludes unwanted models, this is how the current models.png is made:

`py manage.py graph_models --pydot -X AbstractUser,Group,Token,TokenProxy,Session,AbstractBaseSession,TaskResult,LogEntry,Permission,ContentType,ChordCounter,GroupResult -a -g --arrow-shape normal --color-code-deletions -o models.png 
`
