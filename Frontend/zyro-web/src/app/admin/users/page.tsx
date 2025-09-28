"use client";

import ProtectedPage from "@/components/security/ProtectedPage";
import { ManagementPageLayout } from "@/components/layout/ManagementPageLayout";
import AdminUserDepartmentPanel from "@/components/layout/AdminUserDepartmentPanel";

export default function AdminUsersPage() {
  return (
    <ProtectedPage requiredRoles={["Admin"]}>
      <ManagementPageLayout>
        <div className="flex-1 min-h-0">
          <AdminUserDepartmentPanel />
        </div>
      </ManagementPageLayout>
    </ProtectedPage>
  );
}
