[![Build Status](https://travis-ci.com/MarHai/ScrapeBot.svg?branch=master)](https://travis-ci.com/MarHai/ScrapeBot)

# ScrapeBot
ScrapeBot is a tool for so-called "agent-based testing" to automatically visit, modify, and scrape a defined set of webpages regularly. It was built to automate various web-based tasks and keep track of them in a controllable way for academic research, primarily in the realm of computational social science.

This repository allows for actual agent-based testing across a variety of instances (e.g., to vary locations, languages, operating systems, browsers ...) as well as configuring and maintaining these instances. As such, ScrapeBot consists of three major major parts, each of which is included in this repository. If you want to break it down, it consists of the following three parts:

|#|Part|Required|Accessibility|Technology|
|---|---|---|---|---|
|1|*Database*|yes, once|needs to be accessed by all instances and the web frontend|MySQL|
|2|*Instance*|yes, as often as you like|should not be accessible to anybody|Python (+ Selenium)|
|3|*Web frontend*|no, but if you fancy it, then set it up once|should be served through a web server|Python (+ Flask)|

## 1. Installing the database
There is actually not much to do here apart from installing a MySQL server somewhere and make it accessible from outside. Yes, this is the part which everybody warns you about on the internet, but hey ```¯\_(ツ)_/¯```. So go ahead, install it, and remember those credentials. Next, proceed with part 2, installing a new instance. Once you specify the database credentials there, it will create the database tables as necessary if they do not exist yet.
 
## 2. Installing a new Instance
Installation varies depending on your operating system. The most common way to use it, though, would be on a *nix server, such as one from Amazon's Web Services (AWS). Hence, this installation tutorial is geared toward that, although ScrapeBot can also run under other operating systems, including Windows.

#### Installing on Linux/Unix
1. The easiest server version to get started with is a 64-bit Ubuntu [EC2 instance](https://aws.amazon.com), such as AWS' "Ubuntu Server 18.04 LTS" free tier. Launch that and SSH into it.
1. Update the available package-manager repositories. Afterwards, we need to install four things:
    - PIP for the 3.x [Python](https://www.python.org/downloads/) environment
    - A browser of your choice. I'll use [Firefox](https://www.mozilla.org/en-US/firefox/), which is easily avilable through EC2's apt-get repositories.
    - If you are on a Unix system, such as our free EC2 tier, you do not have a GUI but you will need one (or simulate one, for that matter). I'll use an [X11 display](https://en.wikipedia.org/wiki/Xvfb).
    - Git to later get the latest version of ScrapeBot.
    ```
    sudo apt-get update
    sudo apt-get install -y python3-pip firefox xvfb git
    ```
1. Now get (i.e., clone) the latest version of ScrapeBot and change into the newly generated directory.
    ```
    git clone https://github.com/MarHai/ScrapeBot.git
    cd ScrapeBot/
    ```
1. If you are using either Chrome or Firefox, [ChromeDriver](http://chromedriver.chromium.org/) or [Geckodriver](https://github.com/mozilla/geckodriver) are also required. Luckily, I've already integrated them into the ScrapeBot. All you need to do is provide it with execution rights. 
    ```
    chmod u+x lib/*
    ```
1. Next, we install all Python requirements that ScrapeBot has.
    ```
    pip3 install -r requirements.txt
    ```
1. That's it, we should be good to go. Hence, let's configure your newly created instance of the ScrapeBot by following the step-by-step wizard. On Linux, it will end by setting up a cronjob that runs every two minutes. On other systems, you need to ensure that yourself. 
    ```
    python3 setup.py
    ```
    By the way, in running ```setup.py```, also on an already running instance, you can easily create new users.

#### Installing on Windows
Should work fine but keep in mind to either have your preferred browser set in your PATH environment or to specify the paths to your executables in the ```Instance``` section of your ```config.ini```, like so:
```
BrowserBinary = C:\Program Files\Mozilla Firefox\firefox.exe
```
or
```
BrowserBinary = C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
```

#### Installing on a Raspberry Pi (2B+)
Currently available Firefox versions mismatch currently available Geckodriver versions for ARM systems, such as Raspberry Pi. In other words, as long as ```apt-get install firefox-esr``` results in versions below 57, do not bother.

Instead, you can use Chrome. This is in spite of the fact that the therefore needed Chromedriver is a bit old (as Chrome has stopped deploying it for ARM systems) and is thus not capable of taking screenshots.

Finally, note that Selenium and the ScrapeBot require RAM, something the Raspberry Pi is rather short of. As a general take, you should only use ScrapeBot on a RasPi in exceptional cases and without too many recipes running.

***tl;dr**:* *Don't do it unless necessary. And if so, use Chrome but do not take screenshots.* 

## 3. Installing the web frontend
By following the installation guidelines from above, you have also installed all the prerequisites for the web frontend. Despite these prerequisites, though, no web server is yet in place to serve it. This is only required on one instance, obviously, and it can even run on a separate machine without the instance being run regularly. 

The web frontend allows you to overlook instances (see screenshots from the [dashboard](readme_screenshots/dashboard.jpg) and the [instance detail view](readme_screenshots/instance.jpg)), configure recipes (see screenshots from the [recipe detail view](readme_screenshots/recipe.jpg) and the [recipe-step configuration](readme_screenshots/recipe_step.jpg)), export the recipes to replicable `.sbj` files (see a [screenshot of a .sbj file](readme_screenshots/export.jpg)), and check the log files from individual runs (see the [screenshot of a run log](readme_screenshots/run.jpg)).

Here is a short installation guide for the web frontend (again, after (!) you have successfully finished setting up the above).

1. First, we need to install the actual web server, or servers for that matter. As we are dealing with a Python Flask app on Unix, we'll use [gunicorn](https://gunicorn.org/) to serve the Python app internally, [nginx](https://www.nginx.com/) as an external web server, and [supervisor](http://supervisord.org/) to ensure availability.
    ```
    sudo apt-get -y install gunicorn3 supervisor nginx
    ```
1. To make everything accessible via HTTPS, we need to have SSL certificates. For the sake of completeness, we'll self-sign our certificates here; for a production server, you may want to use [Let's Encrypt](https://letsencrypt.org/), for example through [Certbot](https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx).
    ```
    mkdir certs/
    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout certs/key.pem -out certs/cert.pem
    ```
1. Now, we prepare the nginx web server to use these certificates and to listen to incoming requests. I've included an example configuration for this which we can simply copy and use. Be warned, however, that this configuration file requires absolute paths to your home directory, which I assumed to adhere to a "ubuntu" user (as is the default user for AWS Ubuntu instances).
    ```
    sudo rm /etc/nginx/sites-enabled/default
    sudo cp nginx.conf /etc/nginx/sites-enabled/scrapebot
    sudo service nginx reload
    ```
1. The outgoing web server is in place. Yet, for this to be possible, firewall settings may also need adjustment. That is, on AWS, you may need to add inbound security rules for both HTTP and HTTPS.
1. Finally, we can configure gunicorn to be handled by supervisor. Again, this relies on absolute paths to your home directory, so if your user is not called "ubuntu" you should double-check these configuration files. 
    ```    
    sudo cp supervisor.conf /etc/supervisor/conf.d/scrapebot.conf
    sudo supervisorctl reload
    ```
1. This is it, you should now be able to call and work with the web interface (which is incredibly slow under AWS' free tier).

## The almighty "config.ini"
ScrapeBot is configured through two ways. First and foremost is a ```config.ini``` file that sets the connection to the database and the like. This ensures that everything is running and instances and recipes can interact with each other. Second, all the actual agent-based testing stuff is done via the web frontend. Thus, this configuration is stored inside the central database. And while the web frontend helps you in understanding what you can and cannot do, the ```config.ini``` file is not as self-explanatory. The ```setup.py``` helps you in creating one, though. But if you want to know more, here is an overview of all potential settings.
### Database
This section holds only four options, all aimed at connecting to the central database.
- **Host** is the central database host to connect to.
- **User** must hold the username to connect to the central database.
- **Password** holds, well, the according password.
- **Database** represents the database name. Small side note here: The step-by-step wizard Python script (i.e., ```setup.py```) will generate tables and stuff if (and only if) they do not exist yet.
- Due to long runtimes for recipes, ScrapeBot sometimes struggles with MySQL server timeouts (at least, if servers close connections rather strictly). To overcome this problem, you may set **Timeout** here to a number of seconds after which the database connection should be automatically renewed. Best practice here, by the way, is to do nothing until you run into problems. If you do, however, check your MySQL server's timeout and set ScrapeBot's Database/Timeout setting to a value slightly below (e.g., -10) this number: 
  ```
  SHOW SESSION VARIABLES LIKE 'wait_timeout';
  ```
- If you intend to take lots of screenshots, you might want to store them not locally but rather in an [Amazon S3 bucket](https://aws.amazon.com/s3/). For this to happen, you need to specify your Amazon S3 bucket user's credentials (i.e., its access and secret keys). Alternatively (also, additionally), you can specify to store screenshots locally (default; directory specified under Instance). So, in case you want to upload screenshots to Amazon, you need to specify **AWSaccess**, **AWSsecret**, and **AWSbucket** here.

### Email
The web frontend will send emails from time to time. So if you want an instance to serve as web frontend, you need to configure an SMTP server here for it to be able to actually send those emails.
- Again, **Host** is the address of the SMTP (!) server.
- **Port** represents the port through which to connect (typically, this is 25 for non-TLS and 465 or 587 for TLS servers).
- **TLS** should indicate whether a secure TLS connection should be used (1) or not (0).
- **User** is the user to connect to the SMTP server.
- And **Password**, well, again, holds the according password.
### Instance
Finally, a ```config.ini``` file is always unique for one instance. And as such, it specified some of its instance's environmental settings. And while they do differ (depending, for example, on the browser and the operating system), I tried to keep them as unified as possible to make configuration for you as convenient as possible.
- **Name** is especially easy as you can use whatever name you prefer. This is the name the instance will use to register itself against the database. It will thus appear in the web frontend as well as in all downloaded datasets. Keep in mind that this should be unique or otherwise the instance pretends to be something (or somebody) else.
- **Timeout** makes agents more humane in that it specified the amount of seconds between each recipe step (after loading a page finished). As such, it also affects the time an agent needs to perform a recipe. A good balance is a timeout of 1 second. Side note: Actual timeouts will vary randomly around +/-25% to mimic human surf behavior more thoroughly.
- **Browser** is the [Selenium](https://www.seleniumhq.org/projects/webdriver/) webdriver to use. See its [documentation on drivers](https://selenium-python.readthedocs.io/installation.html#drivers) to find out more. Whatever driver you choose, though, it needs to be installed correctly.
- **BrowserBinary** is the path to the binary (if necessary). If your browser is able to run from PATH directly, then this is not necessary.
- **BrowserUserAgent** overwrites, if set, the default [user-agent string](https://en.wikipedia.org/wiki/User_agent#Use_in_HTTP).
- **BrowserLanguage** sets the [accept_languages setting](https://www.w3.org/International/questions/qa-lang-priorities). You can use either languages (e.g., "en", "de") or language+region (e.g., "en-us", "en-gb") settings. 
- **BrowserWidth** and **BrowserHeight** define (in pixels) the size of the browser window to emulate. Use 1024 and 768 if unsure.
- For screenshots to be taken and stored locally, a **ScreenshotDirectory** could be specified. Default is the ```screenshots/``` sub directory. Alternatively, you can upload screenshots to an Amazon S3 bucket. In this case, go ahead and configure *AWSaccess*, *AWSsecret*, and *AWSbucket* under Database, this setting is then ignored.

## Replicability
ScrapeBot offers to export recipes into JSON-encapsulated files. These files are called `.sbj` files (as in **S**crape**B**ot **J**SON) and include all necessary specifications for a recipe, its individual steps and values. Note, that these files do not include any runtime information, such as instances, runs, logs, or collected data.

However, `.sbj` files can also be imported into the system. As such, they depict an easy way to publish replicable recipes for other scholars to build upon.

To get you started easily on ScrapeBot, you can find a couple of import-ready `.sbj` files under [recipes/](recipes).  

## Further information
ScrapeBot uses [Selenium WebDriver](https://www.seleniumhq.org/projects/webdriver/) for its browser emulations. As such, it is capable to run with a broad variety of browsers. 

## Very brief history
The ScrapeBot was available for quite some time as a CasperJS-based tool which was controlled through a bash script. The latest (stable) release of that version is available as [v1.1](https://github.com/MarHai/ScrapeBot/tree/v1.1) of this repository.

## Citation
[Haim, Mario](https://haim.it) (2019): ScrapeBot. A Selenium-based tool for agent-based testing. Source code available at https://github.com/MarHai/ScrapeBot/.
