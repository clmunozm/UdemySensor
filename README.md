# UdemySensor
This sensor uses the Udemy API to retrieve information about the user's courses, such as the course name and progress percentage.

## Prerequisites
* ### **Python**
    Python `3.12` or higher
* ### **bGgames account**
* ### **Udemy account**

## Run with Python
  To run the sensor, use the following command in the console within the file directory:
  ```shell
  python udemySensor.py
  ```

## Login bGames
  Once the sensor starts, it's necessary to log in using your bGames credentials
  (For configuring the bGames cloud module, you can check the following repository: [bGames-module](https://github.com/clmunozm/bGames-module/))

## Get access token
  To obtain the access token from the browser cookies, once logged into Udemy:
    * First, right-click anywhere on the page, then click on “Inspect”
    * Click on “Applications”
    * Click on “Cookies”
    * Then search for “access_token”. It should look like a random string.

  ![screenshot_Udemy](https://github.com/user-attachments/assets/49436507-64e1-449a-a5ea-7506d0064392)

## Wait for the courses to load
  The sensor will fetch the courses from the Udemy API to award one point for every 10% of progress in each course, recording the assigned score to avoid awarding points for previously registered progress. This process may take some time depending on the number of courses the user has.
