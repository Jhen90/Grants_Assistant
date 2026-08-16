
# KICKOFF PROMPT #1

- created: 2026.06.23
- version: 1.1.0

## USER PROMPT 0: 

I want to build a Grants Manager Assistant System that cover the full lifecycle of grants fund-raising process, described in the file "Grant-Research-Application-Assistant-Workflow-v1.0.0.md" as your master prompt.

PROBLEM STATEMENT: The Grants Finding, Funding, and Fulfillment process is TEDIOUS, TIME-CONSUMING, DIFFICULT, and REQUIRES EXTREME EXPERTISE AND EXPERIENCE.  Good grants for a lot of money are scarce, have many logistic, relationship, or political hurdles to overcome.  It takes experience to anticipate barriers, and understand and execute the processes WELL.  Sometimes there are hidden barriers or deadlines. Different grainting agencies and foundations have VERY different process and qualification requiremets.  It is fraught with all kinds of unknowns.  Mastering the process can take decades to learn and improve.  Having an intelligent assistants, analysts, and process managers would make the process much more effciient and successful.  

SOLUTION STATEMENT: (the dual of the PROBLEM STATEMENT)

Use the templates in the SDLC_templates folder for creating the output structure, style, and intent (not content) for the system engineering specfications documents. 

We MUST use good version control practices for every deliverable so that no deliverables are overwritten.  Use semantic versioning and date-time stamps in the headers of all files, so we have good traceability and auditability at the file leevel.  

Deliver all documents incrementally as soon as they are available.  
Make all deliverables MODULAR, NOT monolithic.  DO NOT WAIT UNTIL THE END TO DELIVER.  

Ingest the master prompt file, analyze the content, generate a detailed plan for engineering the application to run as a full stack web application 100% locally at first, with the option to deploy it to a cloud server.  


########################################################## 
# USER PROMPT 2: 

I was not specific enough about the use of AI Agents.  
We want to use AI Agents only for the product development process.  
We DO NOT want paid AI services to be required to use the system for production excution.  
We don't want ongoing expenses for AI services when running it in production. 

Generate the document set again, creating a new version 1.1.0 of each SDLC document. Don't overwrite existing documents.  I renamed the SLDS_templates folder to SDLC_templates folder. 

When you finish the next revisions of the SDLC documents, write out a complete VERBATIM session transcript for this session.  

#########################################################

Code Implementation: 

Software Packages: 

Front-end: Flask, Streamlit, React, or Reflex?  
Analytics: Plotly, Pandas, 
Back-end:  SQLite (MVP 1.0), Postgres (MVP 3.0+)


#########################################################

## USER PROMPT 3: Create the Project Task Implementation Plan

Create the Project Task Implementation Plan that Agents will use to generate the code for v1.1.0 of the application.  

Ingest the attached SDLC docs.  Read and understand them.  
Use the requirements and detailed as a contract for implementation.  
Ask me at 2-3 Clarifying Questions that show me your understanding of the project.  

Wait for me to confirm your plan before you execute it.  

##############################################################

Question 1 — Org Profile Seed Data --> ANSWER
@\Grants_Assistant\00_Project_Planning\Org_Context\Seed Data.docx

I attached the Workflow document that gives you a lot more context for the project.  I also attached the Seed_data documnet in MS-Word format.  

Let me know if that provides for you "the actual Dojo profile content so the agents can hard-code it into the seed from day one".  

Q2-A: Use Option B.  

Q3-A:  Use the detailed design and other artifacts as detailed guidance. Agents may make reasonable implementation decisions within the spirit of the spec.  Stay true to the intent of the SLDC specs.  

Feel free to use multiple agents for more detailed spec writing, code and documentation generation, code and documentation reviewers.  

DO NOT OVERWRITE EXISTING FILES, WORK ON COPIES AND MAKE SURE TO INCLUDE DATETIME STAMPS AND UPDATED SEMANTIC VERSIONS IN FILE HEADERS.   

Update your plan and wait for me to review it.  

####################################################################

The fiscal sponsor will be various community organizations, some of which are 501(c)3 orgs.  We can use the organization named "Teen Empowerment" as the main fiscal sponsor for "The Dojo at SomerNova".  Different community partner organizations will serve as fiscal sponsors on the program-level basis for "The Dojo at SomerNova".   We can make this configurable on a per-grant basis.  
########################################################################################

PROMPT TO ADD GRANT FINDER MODULE(S): 

You didn't understand (or I didn't articulate) a crucial set of capabilities.  

We want GMAS to also be an Expert Grant Opportunity Finder (hunter-gatherer) and Evaluation Assistant to help identify the best-targeted grant opportunities, "best" means largest money for least effort, with 

YOU SAID: 
"""
GMAS doesn't scrape or search for grants automatically — it's a management system, not a discovery engine. The workflow is:

Find grants externally — use these sources to discover opportunities:

Candid/Foundation Directory
Grants.gov (federal)
Massachusetts Cultural Council (state/local)
Funder websites directly (your 15 priority funders are already seeded)
Google: "youth development" "Boston" "grant" "2026" "RFP"
Enter the grant in GMAS — click Enter Grant in the sidebar, fill in the title, funder, deadline, amount, focus areas, and paste the URL. Hit Save Grant.

GMAS automatically:

Checks for duplicates
Scores it 0–10 against your org profile
Classifies the deadline urgency
Advances it to EVALUATED or RECOMMENDED
Review on the Dashboard — urgent deadlines and top-recommended grants appear immediately.

The URL field is the key — paste the RFP link so you always have a direct reference back to the source.
"""


The "Grant Discovery" module is missing.  Flesh out the functinoality and skills of an expert grants finder.  

Grants Discovery Skill is missing

Skill / Expertise Components: 
    Hunter-Gatherer, Evaluator, Ranker, Trade-off Analyzer, Initial Decider. 

