# Tidy-Bot
**Automated Tagging and Renaming for Elements in BI tool**

<div align="center">
  <img src="./img/Tidy_bot.png" alt="Tidy-Bot">
</div>


### tl;dr
Tidy-Bot is a Python-based automation tool that streamlines the organization of items in Metabase. It uses AWS Lambda to run queries, analyze item usage, and tag or rename Metabase elements based on predefined rules and usage data, helping to maintain clarity and organization in our BI tool.


### **Problem**

In our BI tool, Metabase, we have a collection of items—cards, models, and dashboards—that were created by different people over the course of two years without a strict naming policy or guidelines for organization and deletion. To complicate things further, we manage two different products that partially use the same metrics (e.g., active subscriptions). For people familiar with this organically grown structure, it’s possible to find the cards they need. However, for new users or anyone using the search function, it's challenging to locate the right items. The search results may include multiple objects with similar names, making it nearly impossible to determine which product they belong to, whether they are still relevant, or if they are outdated.

### **Solution**

To address this issue, I implemented a new, intuitive folder structure and used Metabase's internal database to gather insights on item usage, such as the last access date, the user, and the database queried. From this usage data, I created specific queries to classify items by product and to identify items that are still actively used, those accessed by current employees, and those that may need to be revisited or deleted. Based on this analysis, we can now tag items accordingly.

To automate this tagging process, I developed a bot that retrieves these usage queries from Metabase, lists the relevant elements, and applies the appropriate tags to each. The nice thing about this bot is the fact, that the definition on what elements should be tagged is done by simply SQL query from within the BI tool. The bot just takes once a day whatever is the result of the queries and tags the items.  

The documentation for this bot is available here.

## Overview

Tidy-Bot is a Python-based automation tool designed to manage the tagging and renaming of Metabase cards and dashboards based on usage data. The automation runs on AWS Lambda and integrates with various AWS services to handle secure API key retrieval, logging, and error reporting, with scheduling managed by AWS EventBridge.

## Project Structure

The Tidy-Bot code consists of two primary files:

- **`tidybot.py`:** Handles core Metabase API interactions, including retrieving SQL queries, processing data, and managing the addition or removal of tags on Metabase items. It also updates item names following predefined rules.
- **`lambda-function.py`:** The entry point for AWS Lambda. This script orchestrates tasks by invoking functions in `tidybot.py`, manages logging, and handles error reporting.

## Key Components

1. **API Key Management**
    
    The script retrieves the Metabase API key from AWS Systems Manager Parameter Store for secure authentication.
    
2. **Data Retrieval and Processing**
    - **Retrieve SQL Queries:** SQL queries are fetched from specified Metabase cards based on their IDs.
    - **Execute and Process Queries:** The script executes these queries via the Metabase API, returning results as Pandas DataFrames.
3. **Tagging and Renaming of Metabase Items**
    
    Based on the query results, Tidy-Bot identifies Metabase cards and dashboards, applies or removes tags, and updates item names. These changes are then pushed back to Metabase via the API.
    
4. **Automated Tagging**
    
    Tidy-Bot uses a predefined set of card IDs to retrieve specific items that require categorization. These IDs are configured within the script.
    
5. **Logging and Error Handling**
    - Execution details and errors are logged to AWS CloudWatch.
    - Errors are reported via Sentry, which sends alerts to a designated Slack channel for visibility.

## Deployment Instructions

To deploy Tidy-Bot in AWS Lambda, follow these steps:

1. Upload `tidybot.py` and `lambda-function.py` to AWS Lambda.
2. Ensure that the following layers are added to the Lambda function:
    - **Sentry Python Serverless SDK** for error monitoring
    - **AWS SDK for Pandas** (Python 3.11, Arm64), a pre-built layer provided by AWS

## Automated Execution

Tidy-Bot can be scheduled for automatic execution using **AWS EventBridge** as a trigger for the Lambda function. Here’s a quick setup guide:

1. **Go to EventBridge**: In the AWS Console, navigate to EventBridge and select "Create Rule."
2. **Configure the Rule**:
    - Name the rule, e.g., “Tidy-Bot-Scheduler.”
    - Choose "Schedule" and select "Cron expression" for custom timing.
3. **Set the Schedule**:
    - Use the following Cron expression to run Tidy-Bot Monday to Friday at 18:00 (UTC):
        
        ```
        0 18 ? * MON-FRI *
        ```
        
4. **Set the Target**:
    - Under "Target," select **AWS Lambda function** and choose the Tidy-Bot Lambda function.

This configuration will automatically trigger Tidy-Bot on weekdays at 18:00 UTC.

## Prerequisites

To connect Tidy-Bot, verify that all required elements in the project setup document are correctly configured. This includes the necessary API credentials, IAM roles, CloudWatch logging groups, Sentry project, and Slack alert channels.

## Summary

Tidy-Bot provides an efficient, automated solution for managing Metabase metadata, helping maintain consistent tagging and naming conventions across cards and dashboards. By leveraging AWS services, it ensures secure and robust operations with effective error handling and reporting.

## License

This project is licensed under the MIT License.
