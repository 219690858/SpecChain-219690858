# Reflection

**Application: Headspace** (Google Play, meditation and mental wellness app)

In this project, I built three pipelines (manual, automated, and hybrid) to turn Headspace user reviews into personas, requirements, and tests. Each pipeline worked differently and had its own pros and cons.

## Differences Between Pipelines

The manual pipeline was done by reading reviews and grouping them by hand. This gave full control over how groups, personas, and requirements were written, but it really took me a lot of time and only covered part of the dataset.

The automated pipeline used scripts and the Groq LLM to generate everything automatically. It was much faster and could cover more data, but the outputs were sometimes too general or not very precise.

The hybrid pipeline combined both. I used automated grouping for better coverage, but rewrote personas, requirements, and tests manually. This made the results more accurate while still saving a lot of time compared to doing everything by hand.

## Clearest Personas

The manual pipeline produced the clearest personas. Since I read the reviews myself, the personas felt more realistic and matched actual user problems.

The automated personas were okay, but sometimes too similar to each other or a bit generic (like “frustrated user”). The hybrid pipeline improved this by cleaning up the automated personas and making them more specific.

## Most Useful Requirements

The hybrid pipeline produced the most useful requirements. They were still structured and testable like the automated ones, but also reflected real issues from the reviews (like crashes, offline problems, and subscription confusion).

Manual requirements were also strong but based on fewer reviews. Automated requirements were sometimes too vague or not clearly connected to real user needs.

## Traceability

The automated and hybrid pipelines had the strongest traceability because they covered almost every review in the dataset. This resulted in higher coverage and more connections between reviews, personas, requirements, and tests. In `metrics/metrics_summary.json`, manual review coverage is about 9% with 141 traceability links, while automated and hybrid are both about 100% coverage with 1,148 links each.

The manual pipeline had lower coverage because I only grouped a subset of reviews, but the connections were easier to understand since everything was written carefully.

## Problems in Automated Outputs

Some issues appeared in the automated pipeline:

- Personas were sometimes repetitive or too generic
- Requirements could be vague or not very specific
- Sometimes, the LLM added details that were not clearly supported by the reviews
- Running the pipeline required handling API limits (like rate limiting)

## Conclusion

Overall, the manual pipeline gave the best quality, but the automated pipeline was much faster. The hybrid pipeline worked best for this project because it balanced coverage and quality by combining both approaches.
