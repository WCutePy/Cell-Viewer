
# Cell Viewer

This application allows the visualization and storing of high throughput microscopic data.
It is used for preliminary analysis to see if the data is interesting for further analysis.

It allows storing and exporting the results of the analysis and comparing multiple files with each other.

The application expects input in a specific format. A file in the format
```
Well,Site,Cell,Substance_1,substance_..,substance_n
B02,1,1,2.7,..,5
C02,1,1,3.1,..,4
```
In a tabular display this would look like
| Well | Site | Cell | Substance_1 | substance_.. | substance_n |
|------|------|------|------------|-------------|-------------|
| B02  | 1    | 1    | 2.7        | ..          | 5           |
| C02  | 1    | 1    | 3.1        | ..          | 4           |


## Installation / Setup

First download or clone the repository.
You will need to either create an emtpy db.sqlite3 file, or configure the database
settings for a more complex database.

There is a file .env.sample, which you will need to turn into
a .env file. This holds the environment variables, which shouldn't be committed to github.
Fill in all the .env variables with suitable variables.

To be able to have the app reachable from outside of the machine its running on,
the values OPEN_PORT and OPEN_URL will need to be set appropriately.

When running docker this all that's needed for setup.

### Manual installation:

First you need to have python 3.12.x installed.
This application runs on 3.12.3

you will need virtualenv, or another dedicated package to create a virtual environment.
`pip install virtualenv`
Then you can create a virtual environment.
`py -m virtualenv env`
now activate the virtual environment, in windows this would be:
`.\env\Scripts\activate`
Then simply
`pip install -r requirements.txt`

The following commands will also need to be done the first time.
`py manage.py migrate`
`python manage.py collectstatic --no-input`
`python manage.py ensure_adminuser --no-input`

To be able to make changes to the tailwind css, one needs to install
`npm install`
`npm run dev`

## Running

### Deploying
To deploy it, besides just running it through docker, you will need to set up
the environment variables. 


### Through docker
Running and launching through Docker is simple, just
`docker-compose up --build`
It should then run at http://localhost:{OPEN_PORT}
If to be found outside of a VM, it will run at OPEN_URL:OPEN_PORT an example is: https://example.com:0000

When having issues launching on docker, or on unix.
As a result to most of the application having been developed on Windows, it might be necessary to
perform a command like `dos2unix *` to get the application to work.
If it is needed running the docker will show 
"invalid option| /bin/bash: -"

### manual Running
To develop on windows you can run 
`.\env\Scripts\activate`
`python manage.py runserver`
By default django will run on http://127.0.0.1:8000/
It's possible to change the port with for example
`py manage.py runserver 8999`

When making changes to the tailwind css you need to have a watcher running in a seperate commandline.
`npx tailwindcss -i ./static/assets/style.css -o ./static/dist/css/output.css --watch`

## Documentation

See [.main_docs.md](docs%2F.main_docs.md) For more details about the documentation of this application.
