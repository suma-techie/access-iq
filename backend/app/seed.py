
from app.database import SessionLocal
from app.models.application import Application
from app.models.application_role import ApplicationRole
from app.models.catalog import CatalogEntry
from app.models.project import Project
from app.models.user import User
from app.security import hash_password

SEED_PASSWORD = "Password@123"

USERS: list[tuple[str, str, str]] = [
    ("rohit.kumar", "Rohit Kumar", "manager"),
    ("priya.sharma", "Priya Sharma", "manager"),
    ("khushi.kumari", "Khushi Kumari", "member"),
    ("arjun.patel", "Arjun Patel", "member"),
    ("ananya.singh", "Ananya Singh", "member"),
    ("vikram.reddy", "Vikram Reddy", "member"),
    ("neha.gupta", "Neha Gupta", "member"),
    ("aditya.rao", "Aditya Rao", "member"),
    ("sneha.iyer", "Sneha Iyer", "member"),
    ("karan.malhotra", "Karan Malhotra", "member"),
    ("pooja.nair", "Pooja Nair", "member"),
    ("rahul.verma", "Rahul Verma", "member"),
    ("divya.menon", "Divya Menon", "member"),
    ("siddharth.joshi", "Siddharth Joshi", "member"),
    ("ishita.chopra", "Ishita Chopra", "member"),
    ("aryan.bhatt", "Aryan Bhatt", "member"),
    ("tanvi.desai", "Tanvi Desai", "member"),
    ("kabir.saxena", "Kabir Saxena", "member"),
    ("meera.pillai", "Meera Pillai", "member"),
    ("yash.agarwal", "Yash Agarwal", "member"),
    ("riya.kapoor", "Riya Kapoor", "member"),
    ("dev.mehta", "Dev Mehta", "member"),
    ("simran.kaur", "Simran Kaur", "member"),
    ("arnav.das", "Arnav Das", "member"),
    ("nisha.rana", "Nisha Rana", "member"),
]

OLD_PLACEHOLDER_EMAILS = ["manager@accessiq.com", "lead@accessiq.com", "member@accessiq.com"]

PROJECTS: list[tuple[str, str, list[tuple[str, str]]]] = [
    (
        "Core Platform",
        "AccessIQ's own platform project",
        [
            ("Billing Service", "Handles invoicing and payments"),
            ("Reporting Portal", "Internal analytics and reporting"),
        ],
    ),
    (
        "Customer Success",
        "Tools the support org uses to help customers",
        [
            ("Support Portal", "Customer-facing support case management"),
            ("Ticketing System", "Internal ticket routing and SLAs"),
        ],
    ),
    (
        "Human Resources",
        "Internal HR and workforce systems",
        [
            ("HR Portal", "Employee records and onboarding"),
            ("Payroll System", "Salary processing and compliance"),
        ],
    ),
    (
        "Data Platform",
        "Company-wide data infrastructure",
        [
            ("Data Warehouse", "Central warehouse for analytics workloads"),
            ("Analytics Pipeline", "ETL jobs feeding the warehouse and dashboards"),
        ],
    ),
    (
        "DevOps Infrastructure",
        "Build, deploy, and observability tooling",
        [
            ("CI/CD Pipeline", "Build and deployment automation"),
            ("Monitoring Stack", "Metrics, logs, and alerting"),
        ],
    ),
]

CATALOG: dict[str, list[tuple[str, str, str]]] = {
    "Support Portal": [
        ("Read access to support cases", "support_cases_read", "low"),
        ("Close or reassign support cases", "support_cases_write", "medium"),
        ("Admin on Support Portal", "support_portal_admin", "high"),
    ],
    "Ticketing System": [
        ("View tickets", "tickets_read", "low"),
        ("Edit ticket routing rules", "tickets_routing_write", "medium"),
    ],
    "HR Portal": [
        ("View employee directory", "hr_directory_read", "low"),
        ("Edit employee records", "hr_records_write", "high"),
    ],
    "Payroll System": [
        ("View payroll reports", "payroll_reports_read", "medium"),
        ("Process payroll runs", "payroll_process", "high"),
    ],
    "Data Warehouse": [
        ("Query warehouse tables (read-only)", "warehouse_read", "low"),
        ("Write to warehouse schemas", "warehouse_write", "medium"),
    ],
    "Analytics Pipeline": [
        ("View pipeline runs", "pipeline_read", "low"),
        ("Trigger or modify pipeline jobs", "pipeline_write", "medium"),
    ],
    "CI/CD Pipeline": [
        ("View build pipelines", "cicd_read", "low"),
        ("Deploy to production", "cicd_deploy_prod", "high"),
    ],
    "Monitoring Stack": [
        ("View dashboards and alerts", "monitoring_read", "low"),
        ("Edit alerting rules", "monitoring_write", "medium"),
    ],
}

ROLE_ASSIGNMENTS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Support Portal", [("siddharth.joshi", "team_lead"), ("ishita.chopra", "qa")]),
    ("Ticketing System", [("aryan.bhatt", "application_owner"), ("tanvi.desai", "developer")]),
    ("HR Portal", [("kabir.saxena", "team_lead"), ("meera.pillai", "business_analyst")]),
    ("Payroll System", [("yash.agarwal", "application_owner"), ("riya.kapoor", "developer")]),
    ("Data Warehouse", [("dev.mehta", "team_lead"), ("simran.kaur", "developer")]),
    ("Analytics Pipeline", [("arnav.das", "application_owner"), ("nisha.rana", "qa")]),
    ("CI/CD Pipeline", [("siddharth.joshi", "devops"), ("ishita.chopra", "developer")]),
    ("Monitoring Stack", [("kabir.saxena", "devops"), ("meera.pillai", "qa")]),
]


def get_or_create_user(db, email: str, display_name: str, global_role: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        if user.global_role != global_role:
            user.global_role = global_role




        user.password_hash = hash_password(SEED_PASSWORD)
        return user
    user = User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(SEED_PASSWORD),
        global_role=global_role,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_project(db, name: str, description: str, created_by) -> Project:
    project = db.query(Project).filter(Project.name == name).first()
    if project is not None:
        return project
    project = Project(name=name, description=description, created_by=created_by.id)
    db.add(project)
    db.flush()
    return project


def get_or_create_application(db, project: Project, name: str, description: str, created_by) -> Application:
    application = db.query(Application).filter(Application.name == name).first()
    if application is not None:
        return application
    application = Application(
        project_id=project.id,
        name=name,
        description=description,
        created_by=created_by.id,
    )
    db.add(application)
    db.flush()
    return application


def get_or_create_catalog_entry(db, application: Application, name: str, key: str, severity: str, created_by) -> None:
    existing = (
        db.query(CatalogEntry)
        .filter(CatalogEntry.application_id == application.id, CatalogEntry.permission_key == key)
        .first()
    )
    if existing is not None:
        return
    db.add(
        CatalogEntry(
            application_id=application.id,
            permission_name=name,
            permission_key=key,
            severity=severity,
            created_by=created_by.id,
        )
    )


def get_or_assign_role(db, application: Application, user: User, role_name: str, assigned_by: User) -> None:
    existing = (
        db.query(ApplicationRole)
        .filter(
            ApplicationRole.application_id == application.id,
            ApplicationRole.user_id == user.id,
            ApplicationRole.role_name == role_name,
            ApplicationRole.revoked_at.is_(None),
        )
        .first()
    )
    if existing is not None:
        return
    db.add(
        ApplicationRole(
            application_id=application.id,
            user_id=user.id,
            role_name=role_name,
            assigned_by=assigned_by.id,
        )
    )


def main() -> None:
    db = SessionLocal()
    try:
        admin = get_or_create_user(db, "admin@accessiq.com", "AccessIQ Admin", "admin")

        users = {
            local: get_or_create_user(db, f"{local}@accessiq.com", display_name, role)
            for local, display_name, role in USERS
        }
        manager = users["rohit.kumar"]

        for email in OLD_PLACEHOLDER_EMAILS:
            old_user = db.query(User).filter(User.email == email).first()
            if old_user is not None:
                old_user.is_active = False

        applications: dict[str, Application] = {}
        for project_name, project_description, apps in PROJECTS:
            project = get_or_create_project(db, project_name, project_description, admin)
            for app_name, app_description in apps:
                applications[app_name] = get_or_create_application(db, project, app_name, app_description, admin)



        billing_app = applications["Billing Service"]
        reporting_app = applications["Reporting Portal"]
        get_or_assign_role(db, billing_app, users["khushi.kumari"], "team_lead", manager)
        get_or_assign_role(db, billing_app, users["arjun.patel"], "application_owner", manager)
        get_or_assign_role(db, billing_app, users["neha.gupta"], "developer", manager)
        get_or_assign_role(db, billing_app, users["aditya.rao"], "developer", manager)
        get_or_assign_role(db, billing_app, users["sneha.iyer"], "qa", manager)
        get_or_assign_role(db, billing_app, users["karan.malhotra"], "devops", manager)
        get_or_assign_role(db, reporting_app, users["ananya.singh"], "team_lead", manager)
        get_or_assign_role(db, reporting_app, users["vikram.reddy"], "application_owner", manager)
        get_or_assign_role(db, reporting_app, users["pooja.nair"], "developer", manager)
        get_or_assign_role(db, reporting_app, users["rahul.verma"], "qa", manager)
        get_or_assign_role(db, reporting_app, users["divya.menon"], "business_analyst", manager)

        for app_name, assignments in ROLE_ASSIGNMENTS:
            application = applications[app_name]
            for local, role_name in assignments:
                get_or_assign_role(db, application, users[local], role_name, manager)

        for app_name, entries in CATALOG.items():
            application = applications[app_name]
            for name, key, severity in entries:
                get_or_create_catalog_entry(db, application, name, key, severity, admin)

        db.commit()

        print("Seed complete. Login with password:", SEED_PASSWORD)
        print(f"  {admin.email:28s} role=admin")
        for local, _, role in USERS:
            print(f"  {local}@accessiq.com".ljust(30), f"role={role}")
        print(f"Projects: {', '.join(p[0] for p in PROJECTS)}")
        print(f"Applications: {', '.join(applications.keys())}")
        print("Deactivated old placeholder accounts:", ", ".join(OLD_PLACEHOLDER_EMAILS))
    finally:
        db.close()


if __name__ == "__main__":
    main()
