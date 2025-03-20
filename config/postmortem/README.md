# Postmortem Documents Collection

## Overview

This directory contains a comprehensive collection of postmortem documents in markdown format that serve as the foundation for generating synthetic incident data in the o11y_evol project. These documents come from various sources including major technology companies, cloud providers, and open-source projects, documenting real-world incidents and their analyses.

## Document Characteristics

- **Format**: All documents are in Markdown format
- **Naming Conventions**: Various naming patterns are used, including:
  - Date-based naming (e.g., `2019_07_11_stripe-outage-technology-payment-processing_index.md`)
  - Simple numeric identifiers (e.g., `1.md`, `2.md`)
  - Descriptive titles (e.g., `A_Byzantine_failure_in_the_real_world.md`)
  - Source-prefixed names (e.g., `blog_2018_07_postmortem-for-malicious-package-publishes.md`)

## Content Structure

The postmortem documents follow various formats, but many include some or all of these sections:

- **Summary/Overview**: Brief description of the incident
- **Impact**: Description of the impact on users and business
- **Timeline**: Chronological sequence of events
- **Root Cause**: Detailed explanation of what caused the incident
- **Resolution**: How the incident was resolved
- **Action Items/Lessons Learned**: Preventive measures to avoid similar incidents

## Usage in the System

These documents are used by the o11y_evol system to:

1. Generate synthetic incident data for analysis and training purposes
2. Extract patterns of real-world failures and their resolutions
3. Provide a knowledge base of incident management practices

The system processes these files through the `init_seed.py` script, which:
- Loads all markdown files (excluding this README)
- Extracts content from each postmortem document
- Generates incident data based on the extracted content

## Contributing New Postmortems

When adding new postmortem documents to this collection:

1. Use Markdown format
2. Include as much structured information as possible (summary, impact, timeline, etc.)
3. Name the file descriptively to indicate its source or content
4. Ensure the content is properly formatted for processing by the system

## Document Sources

The postmortem documents in this collection come from various sources including:

- Official company incident reports
- Engineering blog posts
- Public postmortem analyses
- Conference presentations and case studies

This diverse collection provides a comprehensive view of incident management practices across the industry.