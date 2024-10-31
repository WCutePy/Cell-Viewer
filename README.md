
Current dev notes:

To develop on windows you can run 
`.\env\Scripts\activate`
`npx tailwindcss -i ./static/assets/style.css -o ./static/dist/css/output.css --watch`
`docker run -p 6379:6379 -d redis:7.0.12`
`python manage.py runserver `

this is encouraged during active development, because it was not possible to get live changes of every component using docker yet :c.