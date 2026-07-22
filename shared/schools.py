"""
School list for the trip-details intake form.

Scoped to the beachhead market (NESCAC + peer small liberal-arts colleges with
high international enrollment) rather than every US institution — a searchable
selectbox of ~15 names is far easier to use than free text, and it keeps the
school field consistent enough to group students by in the DSO dashboard.

"Other" lets anyone outside the list continue via the free-text field; the
onboarding form treats that as an escape hatch, not an error.
"""

OTHER = "Other (not listed)"

# NESCAC first — the stated beachhead — then peer schools, alphabetically.
PILOT_SCHOOLS = [
    "Colby College",
    "Bates College",
    "Bowdoin College",
    "Amherst College",
    "Bard College",
    "Carleton College",
    "Connecticut College",
    "Grinnell College",
    "Hamilton College",
    "Haverford College",
    "Middlebury College",
    "Oberlin College",
    "Trinity College",
    "Tufts University",
    "Vassar College",
    "Wellesley College",
    "Wesleyan University",
    "Williams College",
]

SCHOOL_OPTIONS = [""] + PILOT_SCHOOLS + [OTHER]
