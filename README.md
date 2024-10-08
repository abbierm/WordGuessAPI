# WordGuessAPI
#### Video Demo: https://youtu.be/nPj7t-Y--OM

### Description:
WordGuessAPI is a Wordle clone you play via API calls. I created this as a way to test Wordle solvers without needing to manually input their answers into the terminal.  WordGuessAPI is primarily written in Python with a bit of HTML and CSS for the website.  I used Flask as the web framework, SQLAlchemy and SQLite to manage the database, and Pytest to help test my project.


### My project has three major parts:
1. **The Flask app** that runs both the website and the API.  The website allows users to register and view their solver’s stats and the API primarily acts as a way for solver’s to play WordGuess.

2. **The WordGuess game** that picks a 5-letter word and allows users up to 6 guesses to try and figure out the word.  After every guess, the game returns a 5 letter string as feedback.
    - ‘G’ (green) represents that the letter is correct and in the right spot.
    - ‘Y’ (yellow) tells the user the the letter has been used but is in the wrong spot.
    - ‘B’ (black/grey) tells the user that the letter is not in the word.

3. **Two example solvers** to demonstrate how someone would make their own solver to play WordGuessAPI.  One of the solvers uses regex and the other uses a simple culling strategy.

# Quick Start: How to Play

> Before being able to use the WordGuessAPI, users must create an account and verify their email via the website. Then, users must register a new solver from the Solver page.

## There are three main requests needed in order to play WordGuessAPI:

### 1. **Request a token** at 'api/tokens'

Tokens are requested with a BasicAuth header with their registered username and password. The returned API token will allow users to user the API for 30 min until needing to request another token.

    import requests
    from requests.auth import BasicAuth

    auth = BasicAuth(username='fake_username', password='fake_password')
    url = "https://wordguess_api.com/api/tokens"

    r = requests.post(url=url, headers=auth)
    response = r.json()


If the username and password are valid, you will receive a JSON response with a "token" key that you will user inside of the header in the form:

    {"Authorization": "Bearer <your token goes here>"}


### 2. **Start a new game** at 'api/start' endpoint

Each registered solver will have a unique api_id that will be used inside of a request body along with the token authorization header above.

    my_token_header = {"Authorization": "Bearer my_unique_token"}

    post_body = {"solver_id": "my solvers unique api id"}
    start_url = "https://www.wordguess_api.com/api/start"

    start_request = requests.post(
        url=start_url,
        headers=my_token_header,
        json=post_body
    )

    starting_payload = start_request.json()

This api/start request returns a JSON payload with information about the game you started.  This is the same format that will be returned after each guess while playing.


    {
        "game_id": "a unique id used to make guesses",
        "solver name": "the name of your solver",
        "status": "True if game is still being played else False",
        "guess_count": 0,
        "guesses" {},
        "correct_word": "*****",
        "message": "Error message if applicable",
        "results": "None, Won, or Lost"
    }

### 3. **Make a guess** at 'api/guess'

The returned start payload will have a key named "game_id" that will be used inside of a guess request body along with the 5 letter guess.


    {
        "game_id": "unique game id sent back after valid start request",
        "guess": "5 letter guess"
    }


As long as the game is valid, the user will receive the same payload format as the start response. Each guess that the Solver sends will get feedback inside of the "guesses" key. Each guess/feedback pair will be nested together inside of another dictionary with the guess_number as the key.

![Wordle Example Image](app/static/assets/wordle_example.JPG)

If the above example was a WordGuessApi game with a solver named "mySolver" and a game_id of "1111111111111111", the ending payload would look like:

    {
        "game_id": "1111111111111111",
        "solver_name": "mySolver",
        "status": "False",
        "guess_count": 3,
        "guesses":  {
                        "1": {"guess": "great", "feedback": "BYGBY"},
                        "2": {"guess": "tiers", "feedback": "YBGGY"},
                        "3": {"guess": "stern", "feedback": "GGGGG"}
                    }
        "correct_word": "stern",
        "message": "None",
        "result": "Won"
    }

>Note that the "correct_word" value will be asterisked out until the game is over.

# WordGuessAPI Project
## The Flask App
>This section describes the Flask web server side of WordGuessAPI. I also describe the Flask extensions I used that are dependent on an active flask app in order to run.

Inside of my root directory I have a file named wordguess_api.py that imports a function called create_app() from my app/__init__.py file. This create_app() function is what builds the entire application including access to the SQLite database, the routes, and access to the HTTP request and response data that gets passed around freely.

WordGuessAPI has three different blueprints that have their own routes and functions that are nested inside of the main app:

1. **api:** This is where the api routes to play WordGuess exist.  After signing up and authenticating their accounts, users can create a solver that makes get and post requests to the api route and will have their games saved to the database.  Using the api routes users can also get their account stats, solver stats, and view past game data.

2. **auth:** In order to use the api, I require that users sign in and verify their email address.  My auth blueprint handles the email confirmation, logging in, and registering an account, and account info and settings.

3. **main:** The rest of the website including the homepage and the documentation are inside of the main blueprint. This includes the homepage for user’s where they can view their solver’s and their solver’s stats.

### The SQLAlchemy ORM
The flask app also has a database that uses SQLAlchemy as an ORM to store users, solvers, and games.  The ORM (object relational mapper) is basically a way to represent the tables inside of a SQL database using python syntax instead of SQL statements. The models for my database tables live inside of the app/models.py file.

A lot of the logic that controls working with users and solvers directly are methods on the User and Solver tables (which are represented as Python Classes).

For example, below is a small snippet of the User table:


    class User(UserMixin, db.Model):
        id: so.Mapped[int] = so.mapped_column(primary_key=True)
        username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True)
        token: so.Mapped[Optional[str]] = so.mapped_column(
                                        sa.String(32), index=True, unique=True)
        token_expiration: so.Mapped[Optional[datetime]]


        def get_api_token(self, expires_in=3600):
            now = datetime.now(timezone.utc)
            if self.token and self.token_expiration.replace(
                    tzinfo=timezone.utc) > now + timedelta(seconds=60):
                return self.token
            self.token = secrets.token_hex(16)
            self.token_expiration = now + timedelta(seconds=expires_in)
            db.session.add(self)
            return self.token

The rows inside the User table represent an individual user.  If a specific user wants access to the API, they need to request a token.  The flask route 'api/tokens' will query and pull up that user as a class instance and then can directly call the get_api_token() method which saves the token inside of their "token" column.

A lot of the modules are wrapped with SQLAlchemy like flask-login.  The Flask-login module helps keep users logged in while they are on the website and it works by adding a "UserMixin" mixin that gives access to extra methods on top of the User class.

### Authentication/Security
From what I understand, security isn't something a new developer should try to do themselves.  Python and Flask are both mature and have a lot of good implementations of security modules and extensions to help keep the site and user's data safe. In this section I am going to discuss some of the security considerations I used to make WordGuessAPI.

- **Passwords**: Using the werkzeug.security library (that comes with the Flask framework), I hash users passwords using the generate_password_hash() function. User's can change their password using a confirmation token that gets sent to their email.

- **User Information**: The only "sensitive" user data the app collects is their email address and passwords.  Passwords get hashed into the database and emails are only used to confirm users when they register and send account changing requests. WordGuessAPI doesn't have a social aspect meaning user's can't view other user's profiles or Solvers.  The only way to access an individual user's page is by being logged in as that user. POST request form data is sent using the flask wtf library and SQLAlchemy statements which helps prevent injection attackers from accessing data using their own SQL statements.

- **Confirmations**: Any account modifying request requires users to click on a link sent to their email with a time sensitive token. The tokens are generated via the jwt.encode library and gets stored in that user's row in the User table. Below is an example link that would get sent to a user's email if they requested a new password.

        "https://wordguess_api.com/reset_password/<token>"


  The token is basically a key for accessing that user's data in the SQL table so if the user clicks on the URL, it will send the token portion part of the URL as an argument to a static method on the User's table to return the specific User.  At that point, the user is "validated" and can make whatever change they requested.

  Currently the only account modifications I have that utilize the email confirmation tokens are:

  - Reset password
  - Delete account
  - Change email address
  - Account Reset (removes all Sovlers)


- **API Usage**: In order to interact with the API, users have to confirm their email. Then, if the user wants to make api calls they need to request an API token from the 'api/tokens' route with a BasicAuth header. The API token can be used for 30 min before expiring and should be added as a header in the following format:

        {"Authorization": f"Bearer {user's token}"}


  To validate that users have the correct token I used Miguel Grinberg's Flask-HTTPAuth extension that provides a wrapper around routes in order to check the credentials. Inside of the 'app/api/auth.py' file I created instances of httpAuth objects imported from the extension. Then these instances provide wrappers for route functions that require the correct headers.  For example, the verify token wrapper from the token_auth() instance looks like:


        from app import db
        from app.models import User
        from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth

        token_auth = HTTPTokenAuth()

        @token_auth.verify_token
        def verify_token(token):
            return User.check_token(token) if token else None


    Using the verify_token decorator I created a function that checks that the token is valid and returns the associated user.  Then, routes that require the token get decorated with @token_auth.login_required as shown below:

        @bp.route('/start', methods=["POST"])
        @token_auth.login_required
        def start_game():
            json_data = request.get_json()
            user = token_auth.current_user()

            ...

            return payload


    Since the initial token request requires a username and password, having a token is akin to the user logging in.

### Sending Emails
WordGuessAPI only sends emails for account confirmation purposes as stated above. Adding email support was tricky because for some reason the defacto extension in Flask (Flask-Mail) just didn't work for me. I spent 2 weeks trying to trouble shoot what the problem could never figured it out. Eventually I tried a different mail extension and realized it was Pallets Flask-Mail.  I think the community run Pallets Ecosystem has started re-maintaining Flask-Mail but when I tried using it again after the great Flask 3.0 migration it still wasn't working for me.

>* Pallets is the open source org that created Flask and a lot of the extensions that get installed with Flask like jinja and click. Pallets Eco is a community maintained repo for extensions mainly related to Flask.

Like other Flask extensions, you use Flask-Mail by initiating an object with the application inside of the app/__init__.py file. That way, you can store all of the mail specific configuration information with the rest app's config settings. Then, inside the app/email.py file I have a basic send_email() function that gets imported whenever a route needs to send confirmation emails.

For all of the different emails WordGuessAPI could send, I have templates stored inside of the 'templates/email/' directory. These templates use jinja just like the browser html templates Flask uses to render webpages.


### Testing WordGuessAPI with Pytest
What makes testing a Flask app tricky is that the routes, ORM, and many of the extensions need an active application server in order to run. This makes it hard to test individual functions in isolation because they depend on the Flask server.  To get around this Flask and Pytest allow you to create a "test_client" that creates a pure testing application that can be used by the functions for testing. Inside of the wordguess__api/test/conftest.py file there is a test_client() function that gets passed as an argument to the test functions that depend on the active application.

Another cool feature of Pytest is the use of fixtures. Inside of the conftest.py file I can setup different scenarios in order for the tests to access anything that they would need to test.

For example, a lot of the tests depend on the SQLAlchemy database models. Using Pytest fixtures I can initiate a fresh test database pre-loaded with entries inside of a function called init_dd() with a pytest.fixture() decorator.


    #conftest.py

    @pytest.fixture(scope="module")
    def init_database(test_client):
    db.create_all()

        user = User(
                username='user1',
                email='u1@gmail.com',
                confirmed=True
            )
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()

    yield db


Then anytime a test needs to access that pre-loaded database I can pass the "init_db" fixture to the test function.

    #test_model_functions.py

    def test_adding_user(init_database):
        """
        GIVEN pre-filled database
        WHEN a new user is added to the database
        THEN check if user was added and found inside the db.
        """
        user = User(username='user5', email='u5@gmail.com')
        user.set_password('test_password')
        db.session.add(user)
        db.session.commit()
        user_lookup = db.session.scalar(
            db.select(User).where(
                User.username == 'user5'))
        assert user_lookup.username == 'user5'
        assert user_lookup.email == 'u5@gmail.com'

The hardest part of writing tests while building this application was updating the tests as I added new features. I frequently changed my database schema, application routes, and gameplay functions so it seemed like a lot of extra work to go back and fix all the tests to match the changes.  I also spent a lot of time figuring out WHY my tests weren’t working when I could see that my app was working correctly inside of the development server. That is not to say testing is bad or a waste of time but there is definitely a learning curve for using a test framework. I eventually found a good rhythm where I would run and fix the failed tests after making any changes.


### The Frontend Website
WordGuessAPI has a pretty bare-bones basic frontend layout.  I opted to write my own CSS instead of using Bootstrap because I was picky about how it looked.  There is nothing wrong with Bootstrap but after spending a few afternoons trying to figure out how to customize the SASS files I realized it was easier to just learn CSS.

![Landing Page](app/static/assets/index.JPG)

Almost all of the CSS lives inside the app/static/styles.css file. There are a few exceptions where if one specific element needed to be slightly different than it's peers, then I would add a "style" attribute inline to that element's HTML.  Inside the the "styles.css" file I utilized flexbox quite a lot due it being intuitive and easier to accommodate mobile friendly browsing.

The only Javascript I added was a "dark-mode" toggle button that allows users to change the styling to be brighter or darker depending on their preferences. I also used the highlight.js library to stylize the code snippets on the front page. For the actual "toggle", I used an ionicon flashlight button.  The script that does the "toggling" is in the app/static/code/main.js file.  In order to save the user's dark or light mode preference I also have a script tag on the layout.html that fetches the user's dark or light mode preference from their previous session.

## The WordGuessAPI Game
>This section describes the gameplay logic and how games are handled during and after the game is finished.

### Gameplay Logic (wordguess.py)
The actual gameplay logic for WordguessAPI lives inside of the app/wordguess.py file. This is where the information from the routes gets sent to in order to be processed/evaluated before getting updated and sent back to the user. The "brains" behind the game is the game_loop() function that takes the user's game information and new guess and processes the information based on the current state of the game. If the guess is a valid word, the game_loop function will get feedback, check the current number of guesses, and update the user's game. Then the game_loop function will call the create_payload() function and return a JSON response back to the 'api/guess' route. The game_loop() function basically acts as a control flow mechanism that checks the state of the game and updates it depending on conditional statements.

    def game_loop(
        game: GameNode,
        guess: str
    ) -> dict:
        if _validate_guess(guess) == False:
            return create_payload(
                include_feedback=False,
                include_correct=False,
                message="Word not found in our dictionary."
            )
        feedback = _feedback(game.correct_word, guess)
        update_game(game, guess, feedback)

        if game.status == False:
            _add_game_to_db(game)
            payload = create_payload(game=game)
            game_cache.remove(game.game_token)
            return payload
        return create_payload(
                game=game,
                include_correct=False,
                include_feedback=True
        )

### The words
WordGuessAPI has two lists of words that are used throughout the game inside of the app/words/ directory. Originally the lists were in a .txt file but I converted them to Python lists inside of the same-named .py files so I could load them as modules instead of having the game read the words to memory. The scripts I used to modify the plain text files are inside the sort_correct_words.py file.

There are 12000 words inside of correct.py that are used to make sure the client's guesses are valid.  If the guess can't be found inside that list then the program will return an error message saying that the word isn't a valid dictionary word and won't give feedback.

Inside of the words.py file there are around 2000 words in a list that can be possible chosen words as an actual game answer. Like Wordle, this list contains the more commonly known English words and avoids slang, plurals, and words with racially sensitive connotations.


### The Games Cache (games.py)
>This is the file that contains all of the in-memory functionality for games while the games are still active. I wrestled a lot over how to deal with the persistance problem because ideally RESTful APIs shouldn't save states in-between calls.  That being said, it was either this or store the games in the SQLite database which ended up being really slow. The in-memory cache has a lot of problems and is just a quick fix for a bigger problem.  If I were to ever deploy WordGuessAPI in the real world, the in-memory GameCache wouldn't work unless I only deployed one instance of the application.  Basically it doesn't scale and I would need to implement some third party solution like a redis server. But for the scope of this project, I think this GameCache works but I did want to note that I am aware of it's limitations.


The game itself is stored inside of a Pydantic dataclass that is declared inside of this games.py file.  Pydantic is a third party library that makes it easier to validate and convert data from one form to another which makes it especially useful for working with APIs.

    from pydantic import BaseModel

    class GameNode(BaseModel):
        game_token: Optional[str] = None
        token_expiration: Optional[datetime] = None
        solver_name: str
        solver_id: int
        user_id: int
        correct_word: str
        guess_count: int = 0
        guesses: list = []
        feedback: list = []
        status: bool = True
        results: Optional[bool] = None


Inside of the wordguess.py file there is a create_game() function that the 'api/start' route calls that creates a new GameNode and adds the game to the GameCache.

The GamesCache Class is basically an ordered dictionary with some extra methods to help get games based on a "game_token".  When users make guesses the 'api/guess' first checks that the game exists by calling the GameCache's get() method with the "game_token".  If an active game is returned, the cache moves the game to the end of the GameCache's ordered dictionary's entries.  The GameCache has a max size that once it reaches, it will start removing items at the front of the list. The games that haven't been accessed or created last will be removed first.

One of the coolest things about the GameCache was that it helped me understand how modules and flask extensions work. In order for the GameCache to be used, it needs to be initiated as an individual object each time the Flask application is run. This gets tricky when multiple files (including the tests) need to have access to the GameCache instance.  So the solution was manually adding it to the Flask create_app() factory function inside of the app/__init__.py file.  This is where all the blueprints and third party modules are instantiated to be used and imported by the entire application.


## Two Example Solvers
>In this section I describe the basics for how to create a solver and briefly write about the different strategies my solvers use to determine the correct word for WordGuessAPI.

### Basic Solver Requirements

- **Be registered by a confirmed user**
    - Confirmed users have made an account and validated their email address.
    - Each solver has a unique "solver_id" that helps store the solver's information in the database.
    - The solver_id is found, created, or changed on the solver's page.


- **Send POST requests with data inside a JSON form body to the following routes:**

    - https://www.wordguess_api.com/api/tokens
    - https://www.wordguess_api.com/api/start
    - https://www.wordguess_api.com/api/guess

>Note that these full routes are hypothetical assuming I ever serve this application IRL.

- **Parse the responses from the different routes**
    - For example, if your solver correctly guessed a word after sending the "api/guess" request, it should be able to see the the "status" is set to "False" and results set to "Won". Therefore your solver should either end the program or clear out the current games information and start another game.

- **Have a strategy that can use the "G", "Y", and "B" feedback from the previous response to cull a list of words and pick the next word.**
    - A solver will need to have some coded logic to pick it's next guess. In order to do this, there should probably be a plain text file with a list of possible five letter words that get loaded into RAM while the program is running. If certain words aren't possible based on the feedback, the solver should be able to remove that word. The most optimized Wordle strategies take into consideration which letters will have a higher chance of occurring naturally in the English language.

### Regex Solver
My regex solver is object oriented and uses regular expressions to search for words based on the feedback. Although there are a lot of ways to use regular expressions, my solver only uses a few of the patterns:

- **"\w"**  tells the program to find alphabetical characters. For example if I was looking for a word with exactly 5 alphabetical letters I could use the pattern:

        regex_pattern = r"\w\w\w\w\w"

>Note that the r in front of the string tells the Python compiler not to escape whatever comes after the '\\' character.
- **"(?=.*?\<letter>)"** and **"(?!.*?\<letter>)"** Are lookahead symbols that tell the regex compiler to only match objects if they have a specific letter OR don't have a specific letter in the word.  This is especially useful for the yellow feedback letters because it allows the program to put specific patterns in an index while also making sure the word has that letter. For example if I got the feedback "BBYBB" for the guess "GREAT", my next regex pattern would could like:

        regex_pattern = r"(?=.*?e)(?!.*g)(?!.*r)(?!.*a)(?!.*t)\w\w\w\w\w"



- **[^]** the brackets the carrot will tell the regex compiler to only search for words at that index without letters in that spot. Using the same example from above but adding the "[^e]" would be written like:

        regex_pattern = r"(?=.*?e)(?!.*g)(?!.*r)(?!.*a)(?!.*t)\w\w[^e]\w\w"


The regex solver will loop over both the feedback and previous guess to put the individual guess letters into different lists depending on the feedback color.  The green feedback gets sorted directly to the regex pattern so instead of a '\\w' at that index, it would be replaces with the correct letter.  The yellow feedback gets sorted to another list that will be used to create the positive lookaheads and the [^ ] for that letter's index in the guess.  Lastly, the black/grey letters get placed in another list (assuming the letter hasn't been positively placed elsewhere in the guess) to a list that gets iterated through to create the negative lookaheads.

Words get culled from the list using Python's filter and a lambda function. I'm not sure if this is faster than looping though the words and putting them into another list but it does help make the code look syntactically cleaner.

        new_possible_words = list(filer(lambda x: re.match(<regex_pattern>, x), list_of_words))



After creating the new list of possible words, the solver just picks a new word randomly.  I played around will using Python's Counter() class to pick a word based on letter frequencies but when I tested it against just picking a random word, it scored around the same.

This solver on average gets around 88 - 90% of the words correct in an average of 4.5 guesses.  One thing to note is that the list of words both my example solvers use is much larger than the list the game chooses from.  All that to say I think that 90% is a pretty good :)

### Slice and Burn

Slice and burn was the second solver I made to act as a control to compare to my RegexSolver.  It uses a simple culling strategy where it iterates through all of the words to check if they have the right letters. For example, the "culling" of the words based on the "G" green feedback looks like:


        # Green Letters- culls words without matching green letters
        for index, letter in enumerate(self.green_letters):
            if isinstance(letter, str):
                new_words = [word for word in self.words if word[index] == letter]
                self.words = set(new_words)


The cull_words() function will iterate through the possible words list two more times for both the "Y" yellow feedback and "B" black/grey feedback. Its safe to say that this solver on average runs much slower than the regex solver just because it is in fact iterating through each letter in the list of words 3 times.

This "Slice and Burn" solver gets around 85-88% of the words correct with an average of 5.2 guesses.

While I was creating Slice and Burn I wanted to learn how to use the Python logging module so it logs (saves) game data into a .txt file in the logs directory.  I also implemented the Counter() described in the Regex Solver to pick words based on letter frequencies.  For some reason it helped "Slice and Burn" pick the correct word more frequently than without it unlike the tests for regex.

&nbsp;
&nbsp;


## Acknowledgements

>This is a list of helpful resources I used to complete this Project.  Although this section is not part of the requirements from CS50x, I wanted to credit the super helpful resources that I continuously relied on while making WordGuessAPI.


- **The Flask Mega Tutorial, SQLAlchemy2 in Practice, and Flask Web Development** all by Miguel Grinberg.  His tutorials and books helped me learn the ins and outs of the Flask environment including how to integrate important features like SQLAlchemy and user authentication. Most of the logic behind the API tokens came directly from his tutorials.  The Flask Mega tutorial is free on his **[website](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)** but I also highly recommend his **[SQLAlchemy book](https://amzn.to/3S0diwc)** if you were like me and struggled reading the absolute abomination that is the SQLAlchemy documentation.

- **[Testing Flask Applications with Pytest](https://testdriven.io/blog/flask-pytest/)** by Matthew Kennedy.  I taught myself a little Pytest before starting this project but this article really helped me tie in Pytest inside of the Flask application context.  I constantly referenced his gitlab example from the tutorial to see how he was testing things like frontend webpages that required user logins.  The Pytest documentation is pretty good but many of the examples are of the "Foo Bar" variety and out of context with how you would use them in an application.


- My brother in law Andy who looked at this project multiple times over the last year and a half (yes it took me over a year to finish this) giving me good advice and direction. For the most part I feel like I've been learning how to program in a vacuum so having someone to bounce ideas off of and steer me in the right direction was priceless. Andy is a very busy guy so I really appreciate the time he spent looking over my stuff!
