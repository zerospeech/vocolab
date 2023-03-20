import sqlalchemy

tables_metadata = sqlalchemy.MetaData()

_user_id = "users_credentials.id"
_benchmark_id = "benchmarks.label"


""" Table Representing Users"""
users_table = sqlalchemy.Table(
    "users_credentials",
    tables_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String, unique=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("active", sqlalchemy.Boolean),
    sqlalchemy.Column("verified", sqlalchemy.String),
    sqlalchemy.Column("hashed_pswd", sqlalchemy.BLOB),
    sqlalchemy.Column("salt", sqlalchemy.BLOB),
    sqlalchemy.Column("created_at", sqlalchemy.DATETIME)
)

""" 
Table indexing of model ids
"""
models_table = sqlalchemy.Table(
    "models",
    tables_metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, unique=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(_user_id)),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime),
    sqlalchemy.Column("description", sqlalchemy.String),
    sqlalchemy.Column("gpu_budget", sqlalchemy.String),
    sqlalchemy.Column("train_set", sqlalchemy.String),
    sqlalchemy.Column("authors", sqlalchemy.String),
    sqlalchemy.Column("institution", sqlalchemy.String),
    sqlalchemy.Column("team", sqlalchemy.String),
    sqlalchemy.Column("paper_url", sqlalchemy.String),
    sqlalchemy.Column("code_url", sqlalchemy.String),
)


"""
Table indexing the existing evaluators
"""
evaluators_table = sqlalchemy.Table(
    "evaluators",
    tables_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True, autoincrement=True),
    sqlalchemy.Column("label", sqlalchemy.String, unique=True),
    sqlalchemy.Column("host", sqlalchemy.String),
    sqlalchemy.Column("executor", sqlalchemy.String),
    sqlalchemy.Column("script_path", sqlalchemy.String),
    sqlalchemy.Column("executor_arguments", sqlalchemy.String)
)

"""
Table used to index the existing challenges & their metadata
"""
benchmarks_table = sqlalchemy.Table(
    "benchmarks",
    tables_metadata,
    sqlalchemy.Column("label", sqlalchemy.String, unique=True, primary_key=True),
    sqlalchemy.Column("start_date", sqlalchemy.Date),
    sqlalchemy.Column("end_date", sqlalchemy.Date),
    sqlalchemy.Column("active", sqlalchemy.Boolean),
    sqlalchemy.Column("url", sqlalchemy.String),
    sqlalchemy.Column("evaluator", sqlalchemy.Integer, sqlalchemy.ForeignKey("evaluators.id")),
    sqlalchemy.Column("auto_eval", sqlalchemy.Boolean)
)

"""
Table indexing the existing leaderboards and their metadata
"""
leaderboards_table = sqlalchemy.Table(
    "leaderboards",
    tables_metadata,
    sqlalchemy.Column('label', sqlalchemy.String, unique=True, primary_key=True),
    sqlalchemy.Column('benchmark_id', sqlalchemy.String, sqlalchemy.ForeignKey(_benchmark_id)),
    sqlalchemy.Column('archived', sqlalchemy.Boolean),
    sqlalchemy.Column('static_files', sqlalchemy.Boolean),
    sqlalchemy.Column('sorting_key', sqlalchemy.String),
)

""" 
Table entry indexing submissions to challenges
"""
submissions_table = sqlalchemy.Table(
    "benchmark_submissions",
    tables_metadata,
    sqlalchemy.Column("id", sqlalchemy.String, primary_key=True, unique=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(_user_id)),
    sqlalchemy.Column("benchmark_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(_benchmark_id)),
    sqlalchemy.Column("model_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("models.id")),
    sqlalchemy.Column("submit_date", sqlalchemy.DateTime),
    sqlalchemy.Column("status", sqlalchemy.String),
    sqlalchemy.Column("has_scores", sqlalchemy.Boolean),
    sqlalchemy.Column("auto_eval", sqlalchemy.Boolean),
    sqlalchemy.Column("evaluator_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("evaluators.id")),
    sqlalchemy.Column("author_label", sqlalchemy.String)
)

""" Table indexing all leaderboard entries and their location  (as stores json files)"""
leaderboard_entry_table = sqlalchemy.Table(
    "leaderboard_entries",
    tables_metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, unique=True, autoincrement=True),
    sqlalchemy.Column("data", sqlalchemy.JSON),
    sqlalchemy.Column("entry_path", sqlalchemy.String),
    sqlalchemy.Column("submission_id", sqlalchemy.String, sqlalchemy.ForeignKey("benchmark_submissions.id")),
    sqlalchemy.Column("leaderboard_id", sqlalchemy.String, sqlalchemy.ForeignKey("leaderboards.label")),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey(_user_id)),
    sqlalchemy.Column("submitted_at", sqlalchemy.DATETIME)
)