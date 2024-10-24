# <u> Library management Application</u>

**This project is for library stock and customer management**

**<u>This is the backend python script for its server logic</u>**

<br> This is the link to the Frontend ---->>> [Project frontend](https://github.com/shanaor/frontend_library_project?tab=readme-ov-file)

<br> ***Important!!!!*** I used HTML Input restrictions which made some codes in the backend unnecessary , but I left them in because at thier base they are correct as part of correct server actions for a library.

## <br><u>It has the following features:</u>

1. add customer
2. Deactivate customer
3. Add book
4. Deactivate book
5. Change book quantity
6. Loan a book
7. Return loans
8. Get notifications for late return
9. Search existing customers (deactivated and activated)
10. Search existing books (deactivated and activated)
11. Get a list of late loans
12. Get a list of all Returned books
13. list of existing loans including date and time
14. Get store stock, Customer and loan Statistics
15. Get Log information about actions performed in the application by the users sorted by dates
16. And Reset Data to 5 automatic customers and books

### <u>additional features in the script</u>
I organized it by sections using comment command and I used a log file to log every action response to the frontend requests. <br>
I made comments as detailed as possible when in the beginning I explain every line and later when its repetitive I added less comments
assuming the pattern is already recognized. <br>

Some of the SQLAlchemy commands are the new style of writing that is entering slowly in Use - The: **db.session.{command}(table class, requested variable)** <br> So please be aware and not confused.

###  Logging 
Logging is made into the Log file -- BUT ALSO - into the DataBase. <br>
Using it in the ***Log_action method*** It is used to allow the Library owner to track the actions happening in his store so he could make his conclusions about employees and stock and even has bootstrap card presenting the Logs (and thats why it has HTML tags, to style the cards)

###  The alert message 
The index API (/) has a late loan check so when in case of a late loan it would notify the worker about late loan that went into effect. 

###  Help Methods  
to convert the time properly I created 2 time converter methods to present the date as dd/mm/yy, and canceled the time in some place but allowed it in cases like Loans so the users could see the second because - Technically.... - a Loan can be returned at the last moment. so showing the seconds can give the users ability to see why it might be considered a late loan. 

### DataBase Reset

By request an option to Erase all the DataBase and creating 5 default Books and customers was made (located at the end)

### Last remarks 
Global Error catchers were made (in the end) and at the bottom, after Main and under the name **Notes**, I left a route mapping debug command if you happen to need. 
____


### <u>Import used in the backend python</u>

-    astroid==3.3.4
-   blinker==1.8.2
-    click==8.1.7
-    colorama==0.4.6
-    dill==0.3.9
-    Flask==3.0.3
-    Flask-Cors==5.0.0
-    Flask-SQLAlchemy==3.1.1
-    greenlet==3.1.0
-    isort==5.13.2
-    itsdangerous==2.2.0
-    Jinja2==3.1.4
-    markdown-it-py==3.0.0
-    MarkupSafe==2.1.5
-    mccabe==0.7.0
-    mdurl==0.1.2
-    platformdirs==4.3.6
-    Pygments==2.18.0
-    SQLAlchemy==2.0.34
-    tomlkit==0.13.2
-    typing_extensions==4.12.2
-    Werkzeug==3.0.4
-    gunicorn==20.1.0