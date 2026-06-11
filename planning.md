# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:
It searches listings for the items that the user asked for. It returns the listings for the user.**

**Input parameters:
- `description` (str): describes what the user is looking for
- `size` (str): size of item
- `max_price` (float): price of item
**

**What it returns:
A list of matching listing dicts, sorted by relevance (best match first).
Returns an empty list if nothing matches — does NOT raise an exception.**

**What happens if it fails or returns nothing:
No results match the query**

---

### Tool 2: suggest_outfit

**What it does:
Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.**

**Input parameters:
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the item the user is considering buying.
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty.**

**What it returns:
A string with outfit suggestions.
If the wardrobe is empty, offer general styling advice for the item
rather than raising an exception or returning an empty string.**

**What happens if it fails or returns nothing:
Wardrobe is empty**

---

### Tool 3: create_fit_card

**What it does:
Generate a short, shareable outfit caption for the thrifted find.**

**Input parameters:
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): The outfit suggestion string from suggest_outfit()**

**What it returns:
If the outfit is empty or missing, return a descriptive error message
string — do NOT raise an exception.**

**What happens if it fails or returns nothing:
 Outfit input is missing or incomplete**

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?
It checks the logs of each item and moves on to the next step.**

---

## State Management

**How does information from one tool get passed to the next?
With state tracking, it logs each item as checked before moving on to the next and maintains a list of results. Information has to flow to the next tool before the user reenters information.**

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Returns an empty list if nothing matches|
| suggest_outfit | Wardrobe is empty | if wardrobe is empty, general styling advice for the item|
| create_fit_card | Outfit input is missing or incomplete | return error message|

---

## Architecture

<img width="3094" height="7367" alt="image" src="https://github.com/user-attachments/assets/a33639b8-c81e-44ae-b60b-b334f3a33974" />


---

## AI Tool Plan

I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
search_listings() using load_listings() from the data loader — then test it against 3 queries


**Milestone 3 — Individual tool implementations: Use search_listings to look for what the user is looking for and return the listing. The parameters involved are the description, size, and price. 
suggest_outfit returns the complete outfits with parameters such as new item and wardrobe. create_fit_card shows the outfit the user is looking for and returns a message using the parameter of outfit.
**


**Milestone 4 — Planning loop and state management: After search_listings runs, check if results are empty. If yes, set an error message in the session and return early. If no, set selected_item = results[0] and proceed to suggest_outfit.
After suggest_outfit runs, it checks for the items the person is looking for and suggests different options. If no, the wardrobe empty function will run and proceed to create_fit_card. After create_fit_card runs, it returns a message that shows the result of the query with the result from the suggest_outfit tool; if not, it will return incomplete or missing outfit.
**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query: "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"**

**Step 1:
The agent looks for clothes stores using an ID. It uses a tool called search_listings to find vintage stores.**

**Step 2:
It returned the vintage clothes stores. The next tool call is suggest_outfit to give vintage clothes options.**

**Step 3:
It would return the vintage clothes that are available. The next tool call is create_fit_card, which shows whether they are available.**

**Final output to user:
Shows whether it is available or not.**
