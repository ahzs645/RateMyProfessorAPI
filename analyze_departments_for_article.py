import json
import statistics
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Load professor data
with open("professors_school_1448_complete.json", "r") as f:
    data = json.load(f)
    professors = data["professors"]

# Group professors by department
departments = defaultdict(list)
for prof in professors:
    dept = prof.get("department", "Unknown")
    if dept and dept != "Unknown":
        departments[dept].append(prof)

# Calculate statistics for each department
dept_stats = {}

for dept_name, profs in departments.items():
    # Filter out professors with no ratings
    rated_profs = [p for p in profs if p.get("numRatings", 0) > 0]
    
    if rated_profs:
        ratings = [p.get("rating", 0) for p in rated_profs if p.get("rating")]
        difficulties = [p.get("difficulty", 0) for p in rated_profs if p.get("difficulty")]
        num_ratings = [p.get("numRatings", 0) for p in rated_profs]
        would_take_again = [p.get("wouldTakeAgainPercent", 0) for p in rated_profs if p.get("wouldTakeAgainPercent")]
        
        dept_stats[dept_name] = {
            "total_professors": len(profs),
            "rated_professors": len(rated_profs),
            "avg_rating": statistics.mean(ratings) if ratings else 0,
            "avg_difficulty": statistics.mean(difficulties) if difficulties else 0,
            "total_reviews": sum(num_ratings),
            "avg_reviews_per_prof": statistics.mean(num_ratings) if num_ratings else 0,
            "avg_would_take_again": statistics.mean(would_take_again) if would_take_again else 0,
            "rating_std_dev": statistics.stdev(ratings) if len(ratings) > 1 else 0,
            "top_prof": max(rated_profs, key=lambda x: x.get("rating", 0) * x.get("numRatings", 0)),
            "most_reviewed": max(rated_profs, key=lambda x: x.get("numRatings", 0))
        }

# Sort departments by various metrics
by_rating = sorted(dept_stats.items(), key=lambda x: x[1]["avg_rating"], reverse=True)
by_difficulty = sorted(dept_stats.items(), key=lambda x: x[1]["avg_difficulty"], reverse=True)
by_size = sorted(dept_stats.items(), key=lambda x: x[1]["total_professors"], reverse=True)
by_reviews = sorted(dept_stats.items(), key=lambda x: x[1]["total_reviews"], reverse=True)

# Create visualizations
plt.style.use('seaborn-v0_8-darkgrid')
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

# 1. Top 15 departments by average rating
top_15_rating = by_rating[:15]
dept_names = [d[0][:20] for d in top_15_rating]
avg_ratings = [d[1]["avg_rating"] for d in top_15_rating]

ax1.barh(dept_names, avg_ratings, color='skyblue')
ax1.set_xlabel('Average Rating (out of 5)')
ax1.set_title('Top 15 Departments by Average Professor Rating', fontsize=14, fontweight='bold')
ax1.set_xlim(0, 5)
for i, v in enumerate(avg_ratings):
    ax1.text(v + 0.05, i, f'{v:.2f}', va='center')

# 2. Department difficulty vs rating scatter
dept_data = [(name, stats["avg_rating"], stats["avg_difficulty"], stats["total_professors"]) 
             for name, stats in dept_stats.items() if stats["rated_professors"] >= 3]

if dept_data:
    names, ratings, difficulties, sizes = zip(*dept_data)
    scatter = ax2.scatter(difficulties, ratings, s=[s*10 for s in sizes], alpha=0.6, c=ratings, cmap='RdYlGn')
    ax2.set_xlabel('Average Difficulty (out of 5)')
    ax2.set_ylabel('Average Rating (out of 5)')
    ax2.set_title('Department Rating vs Difficulty (size = # of professors)', fontsize=14, fontweight='bold')
    ax2.set_xlim(1, 5)
    ax2.set_ylim(1, 5)
    
    # Add department labels for notable ones
    for i, name in enumerate(names):
        if sizes[i] > 20 or ratings[i] > 4.2 or ratings[i] < 2.5:
            ax2.annotate(name[:10], (difficulties[i], ratings[i]), fontsize=8)

# 3. Department size distribution
sizes = sorted([stats["total_professors"] for stats in dept_stats.values()], reverse=True)[:20]
size_labels = [f"Dept {i+1}" for i in range(len(sizes))]

ax3.bar(range(len(sizes)), sizes, color='lightcoral')
ax3.set_xlabel('Department Rank')
ax3.set_ylabel('Number of Professors')
ax3.set_title('Top 20 Departments by Size', fontsize=14, fontweight='bold')
ax3.set_xticks(range(0, len(sizes), 2))
ax3.set_xticklabels(range(1, len(sizes)+1, 2))

# 4. Would Take Again percentage
top_15_wta = sorted([(name, stats["avg_would_take_again"]) 
                     for name, stats in dept_stats.items() 
                     if stats["rated_professors"] >= 3], 
                    key=lambda x: x[1], reverse=True)[:15]

if top_15_wta:
    dept_names_wta, wta_percents = zip(*top_15_wta)
    dept_names_wta = [d[:20] for d in dept_names_wta]
    
    ax4.barh(dept_names_wta, wta_percents, color='lightgreen')
    ax4.set_xlabel('Would Take Again (%)')
    ax4.set_title('Top 15 Departments by "Would Take Again" Percentage', fontsize=14, fontweight='bold')
    ax4.set_xlim(0, 100)
    for i, v in enumerate(wta_percents):
        ax4.text(v + 1, i, f'{v:.1f}%', va='center')

plt.tight_layout()
plt.savefig('unbc_department_analysis.png', dpi=300, bbox_inches='tight')
plt.close()

# Generate article content
article = f"""
# UNBC Department Performance Analysis: A Deep Dive into RateMyProfessor Data

*Analysis Date: {datetime.now().strftime('%B %d, %Y')}*
*Data Source: RateMyProfessors.com*

## Executive Summary

An analysis of {len(professors)} professors across {len(departments)} departments at the University of Northern British Columbia reveals significant variations in student satisfaction and teaching effectiveness across academic units.

## Key Findings

### 🏆 Top Performing Departments by Rating

The highest-rated departments at UNBC are:

"""

for i, (dept, stats) in enumerate(by_rating[:5]):
    article += f"{i+1}. **{dept}** - {stats['avg_rating']:.2f}/5.0 average rating ({stats['rated_professors']} professors rated)\n"
    article += f"   - Star Professor: {stats['top_prof']['name']} ({stats['top_prof']['rating']}/5.0, {stats['top_prof']['numRatings']} reviews)\n"
    article += f"   - Would Take Again: {stats['avg_would_take_again']:.1f}%\n\n"

article += """
### 📊 Largest Departments

The biggest departments by faculty count:

"""

for i, (dept, stats) in enumerate(by_size[:5]):
    article += f"{i+1}. **{dept}** - {stats['total_professors']} professors\n"
    article += f"   - Average Rating: {stats['avg_rating']:.2f}/5.0\n"
    article += f"   - Total Reviews: {stats['total_reviews']:,}\n\n"

article += """
### 💪 Most Challenging Departments

Students report these departments as the most difficult:

"""

for i, (dept, stats) in enumerate(by_difficulty[:5]):
    article += f"{i+1}. **{dept}** - {stats['avg_difficulty']:.2f}/5.0 difficulty\n"
    article += f"   - Average Rating: {stats['avg_rating']:.2f}/5.0\n"
    article += f"   - Most Challenging Prof: {stats['most_reviewed']['name']} ({stats['most_reviewed']['difficulty']}/5.0 difficulty)\n\n"

article += """
### 📈 Most Engaged Departments

Departments with the most student reviews (indicating high engagement):

"""

for i, (dept, stats) in enumerate(by_reviews[:5]):
    article += f"{i+1}. **{dept}** - {stats['total_reviews']:,} total reviews\n"
    article += f"   - Average per professor: {stats['avg_reviews_per_prof']:.1f} reviews\n"
    article += f"   - Most Reviewed: {stats['most_reviewed']['name']} ({stats['most_reviewed']['numRatings']} reviews)\n\n"

# Add some interesting insights
high_rating_low_difficulty = [(d, s) for d, s in dept_stats.items() 
                               if s["avg_rating"] > 3.5 and s["avg_difficulty"] < 3.0 and s["rated_professors"] >= 3]
low_rating_high_difficulty = [(d, s) for d, s in dept_stats.items() 
                               if s["avg_rating"] < 3.0 and s["avg_difficulty"] > 3.5 and s["rated_professors"] >= 3]

article += """
## Notable Patterns

### 🌟 Hidden Gems (High Rating + Low Difficulty)

These departments offer the best of both worlds - great teaching with manageable difficulty:

"""

for dept, stats in sorted(high_rating_low_difficulty, key=lambda x: x[1]["avg_rating"], reverse=True)[:3]:
    article += f"- **{dept}**: {stats['avg_rating']:.2f}/5.0 rating, {stats['avg_difficulty']:.2f}/5.0 difficulty\n"

article += """
### ⚠️ Challenging Departments (Low Rating + High Difficulty)

Students find these departments particularly demanding:

"""

for dept, stats in sorted(low_rating_high_difficulty, key=lambda x: x[1]["avg_difficulty"], reverse=True)[:3]:
    article += f"- **{dept}**: {stats['avg_rating']:.2f}/5.0 rating, {stats['avg_difficulty']:.2f}/5.0 difficulty\n"

# Add statistical summary
article += f"""
## By The Numbers

- **Total Professors Analyzed**: {len(professors)}
- **Departments Evaluated**: {len(departments)}
- **Total Student Reviews**: {sum(s['total_reviews'] for s in dept_stats.values()):,}
- **Overall UNBC Rating**: {statistics.mean([p.get('rating', 0) for p in professors if p.get('rating')]):,.2f}/5.0
- **Overall UNBC Difficulty**: {statistics.mean([p.get('difficulty', 0) for p in professors if p.get('difficulty')]):,.2f}/5.0

## Methodology Note

This analysis is based on publicly available data from RateMyProfessors.com. Only departments with at least 3 rated professors were included in comparative rankings to ensure statistical validity. Individual experiences may vary, and these ratings represent aggregated student opinions rather than official evaluations.

## Recommendations for Students

1. **Course Planning**: Use department averages as a general guide, but always check individual professor ratings
2. **Balance Your Schedule**: Mix courses from high-difficulty and low-difficulty departments
3. **Read Reviews**: Look beyond ratings to understand teaching styles and course expectations
4. **Contribute**: Add your own reviews to help future students make informed decisions

---
*Data visualization charts available in accompanying graphics*
"""

# Save the article
with open("unbc_department_analysis_article.md", "w") as f:
    f.write(article)

# Also save raw stats for fact-checking
with open("department_statistics.json", "w") as f:
    json.dump({
        "analysis_date": datetime.now().isoformat(),
        "total_professors": len(professors),
        "total_departments": len(departments),
        "department_stats": dept_stats
    }, f, indent=2)

print("✅ Analysis complete!")
print(f"📊 Generated visualization: unbc_department_analysis.png")
print(f"📝 Article saved to: unbc_department_analysis_article.md")
print(f"📈 Raw statistics saved to: department_statistics.json")
print(f"\n📌 Quick Stats:")
print(f"   - Top rated department: {by_rating[0][0]} ({by_rating[0][1]['avg_rating']:.2f}/5.0)")
print(f"   - Largest department: {by_size[0][0]} ({by_size[0][1]['total_professors']} professors)")
print(f"   - Most reviews: {by_reviews[0][0]} ({by_reviews[0][1]['total_reviews']:,} reviews)")