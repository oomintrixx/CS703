# Graduate Project Proposal — Predicting Parking Pressure Across New York City

Prepared for: Mr. N., Data Mining & Data Science
Prepared by: Chen-Wei Weng
Date: September 11, 2026

This project proposes a data-mining study of where and when parking is hardest to find in New York City. Because the city does not publish live parking occupancy, I will use a large, public proxy for parking pressure: the millions of parking violations issued each year, whose density in space and time reflects how contested the curb is. The goal is a model that estimates, for a given area and time, how difficult parking is likely to be — and, ultimately, a simple tool that steers a driver toward easier options nearby. Below I describe the business issue, the modeling approach and its central assumption, the major kinds of information involved, the specific public data sources, and why I want to work on it.

## Business Issue

Hunting for a parking spot in New York wastes enormous amounts of driver time, fuel, and patience, and the resulting "cruising" adds measurably to congestion and emissions in already-dense neighborhoods. Several parties have a real stake in reducing that friction: the city's transportation agency wants less congestion and cleaner air; delivery and service fleets lose paid hours to the curb hunt; and a navigation or mobility app could add a "where is parking easiest right now?" feature to win and keep users. The concrete, repeatable decision the project supports is this: at this time and place, is parking likely to be hard — and where nearby is it likely to be easier?

## Proposed Approach (the Data-Science Core)

New York publishes no direct measure of open spaces, so I will model parking pressure using the density of parking violations as an observable signal, combined with meter locations and rates, street geography, the time of day and week, weather, and nearby events. I will aggregate violations to a spatial unit (police precinct, or a geocoded blockface for finer detail) and a time window, then predict a pressure score for each unit and time. I will begin with interpretable baselines (historical averages by area and hour) and progress to gradient-boosted trees that capture the strong daily and weekly seasonality, evaluating with a time-based train/test split so the model never uses the future to predict the past.

**Central assumption**, stated plainly because it defines the project: violation density reflects a mix of parking demand and enforcement intensity — not availability directly. A block can show many tickets because it is popular, or simply because it is heavily patrolled. A major part of the work is separating those effects: for example, normalizing for enforcement patterns and validating the pressure signal against independent indicators such as meter rates and land use. Handling this honestly is what makes it a data-science project rather than a mapping exercise.

## Information Needed (Major Entities)

The major entities the project would draw on are:

- **Parking-violation events** — each with a time, a location (street and house number, or precinct/borough), and a violation type; their volume and pattern are the core signal.
- **Parking infrastructure** — metered blockfaces and municipal facilities, with their rates, hours, and regulations.
- **Street and area geography** — the blockfaces, precincts, and neighborhoods used to aggregate and map results.
- **Temporal context** — time of day, day of week, and a holiday / street-cleaning calendar.
- **External demand drivers** — weather and nearby events or points of interest that push parking demand up or down.

The specific public sources I expect to use are listed next.

## Candidate Data Sources (Feasibility Preview)

Included as a feasibility preview; I will formalize and validate these in the companion data assignment. All are free and public.

- **Parking-violation events** — primary signal. Parking Violations Issued (Fiscal Year) on NYC Open Data — the time, location, and type of every ticket (~10M+ per year); cross-checked against Open Parking and Camera Violations.
- **Parking infrastructure.** Parking Meters Locations and Status and ParkNYC blockface rates — where metered parking exists, plus its rates and hours.
- **Spatial units and geocoding.** NYPD precinct boundaries for coarse aggregation, with NYC DCP LION / Street Centerline (or OpenStreetMap) to geocode street and house number down to individual blockfaces.
- **Street-cleaning and holiday calendar.** NYC DOT Alternate Side Parking suspension calendar — street-cleaning rules drive a large share of tickets, so this is a key control variable, combined with the U.S. federal-holiday calendar.
- **Weather.** Open-Meteo — free historical hourly weather for New York (NOAA is an alternative).
- **Events and demand spikes.** NYC Permitted Event Information (parades, street fairs, festivals), plus major-venue concerts and games via the Ticketmaster Discovery API.

## Why I Chose This Project

My main reason is genuine interest: parking in New York is a problem I run into constantly, and I have long suspected the difficulty is patterned and predictable rather than random. I am curious whether the intuition every New Yorker has — this block at this hour is hopeless — actually shows up in the data.

I am also drawn to the challenge in the data itself. Turning a messy, indirect signal (tickets) into something meaningful about availability is a real data-mining problem, not a clean textbook one, and separating demand from enforcement is exactly the kind of reasoning I want to get better at. Finally, the problem is concrete and testable, with clear baselines to beat. I am glad to narrow the scope — for instance, to one borough or to metered blocks only — based on your feedback and on what proves practical.

The companion data assignment will formalize and validate these sources — their access method, size, and refresh cadence. Thank you for reviewing — I would welcome your comments on scope and on how far to push the enforcement-versus-demand question.
