from uuid import uuid4

from services.admin_service import AdminService
from services.dependencies import AdminServiceDependencies


def test_admin_service_list_users_passes_filters():
    expected_db = object()
    expected_tenant_id = uuid4()

    class FakeUserRepository:
        def admin_list(
            self,
            db_session,
            email_contains,
            role,
            tenant_id,
            limit,
            offset,
        ):
            assert db_session is expected_db
            assert email_contains == "demo"
            assert role == "ADMIN"
            assert tenant_id == expected_tenant_id
            assert limit == 5
            assert offset == 10
            return ["u1"]

    class DummyTenantRepository:
        def admin_list(self, db_session, name_contains, plan, limit, offset):
            raise AssertionError("not used")

    class DummyDataFreshnessRepository:
        def list_all(self, db_session):
            raise AssertionError("not used")

    class DummyReportJobsRepository:
        def admin_list(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            raise AssertionError("not used")

    service = AdminService(
        AdminServiceDependencies(
            user_repository=FakeUserRepository(),
            tenant_repository=DummyTenantRepository(),
            data_freshness_repository=DummyDataFreshnessRepository(),
            report_jobs_repository=DummyReportJobsRepository(),
        )
    )
    result = service.list_users(
        expected_db,
        email_contains="demo",
        role="ADMIN",
        tenant_id=expected_tenant_id,
        limit=5,
        offset=10,
    )
    assert result == ["u1"]


def test_admin_service_list_tenants_passes_filters():
    expected_db = object()

    class FakeTenantRepository:
        def admin_list(self, db_session, name_contains, plan, limit, offset):
            assert db_session is expected_db
            assert name_contains == "Acme"
            assert plan == "starter"
            assert limit == 2
            assert offset == 0
            return ["t1"]

    class DummyUserRepository:
        def admin_list(
            self,
            db_session,
            email_contains,
            role,
            tenant_id,
            limit,
            offset,
        ):
            raise AssertionError("not used")

    class DummyDataFreshnessRepository:
        def list_all(self, db_session):
            raise AssertionError("not used")

    class DummyReportJobsRepository:
        def admin_list(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            raise AssertionError("not used")

    service = AdminService(
        AdminServiceDependencies(
            user_repository=DummyUserRepository(),
            tenant_repository=FakeTenantRepository(),
            data_freshness_repository=DummyDataFreshnessRepository(),
            report_jobs_repository=DummyReportJobsRepository(),
        )
    )
    result = service.list_tenants(
        expected_db, name_contains="Acme", plan="starter", limit=2, offset=0
    )
    assert result == ["t1"]


def test_admin_service_list_dataset_freshness_calls_repo():
    expected_db = object()

    class FakeDataFreshnessRepository:
        def list_all(self, db_session):
            assert db_session is expected_db
            return ["df1", "df2"]

    class DummyUserRepository:
        def admin_list(
            self,
            db_session,
            email_contains,
            role,
            tenant_id,
            limit,
            offset,
        ):
            raise AssertionError("not used")

    class DummyTenantRepository:
        def admin_list(self, db_session, name_contains, plan, limit, offset):
            raise AssertionError("not used")

    class DummyReportJobsRepository:
        def admin_list(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            raise AssertionError("not used")

    service = AdminService(
        AdminServiceDependencies(
            user_repository=DummyUserRepository(),
            tenant_repository=DummyTenantRepository(),
            data_freshness_repository=FakeDataFreshnessRepository(),
            report_jobs_repository=DummyReportJobsRepository(),
        )
    )
    result = service.list_dataset_freshness(expected_db)
    assert result == ["df1", "df2"]


def test_admin_service_list_report_jobs_passes_filters():
    expected_db = object()
    expected_tenant_id = uuid4()

    class FakeReportJobsRepository:
        def admin_list(
            self,
            db_session,
            tenant_id,
            status,
            city,
            country,
            business_type,
            limit,
            offset,
        ):
            assert db_session is expected_db
            assert tenant_id == expected_tenant_id
            assert status == "COMPLETED"
            assert city == "Toronto"
            assert country is None
            assert business_type == "restaurant"
            assert limit == 10
            assert offset == 0
            return ["job1"]

    class DummyUserRepository:
        def admin_list(
            self,
            db_session,
            email_contains,
            role,
            tenant_id,
            limit,
            offset,
        ):
            raise AssertionError("not used")

    class DummyTenantRepository:
        def admin_list(self, db_session, name_contains, plan, limit, offset):
            raise AssertionError("not used")

    class DummyDataFreshnessRepository:
        def list_all(self, db_session):
            raise AssertionError("not used")

    service = AdminService(
        AdminServiceDependencies(
            user_repository=DummyUserRepository(),
            tenant_repository=DummyTenantRepository(),
            data_freshness_repository=DummyDataFreshnessRepository(),
            report_jobs_repository=FakeReportJobsRepository(),
        )
    )
    result = service.list_report_jobs(
        expected_db,
        tenant_id=expected_tenant_id,
        status="COMPLETED",
        city="Toronto",
        country=None,
        business_type="restaurant",
        limit=10,
        offset=0,
    )
    assert result == ["job1"]
