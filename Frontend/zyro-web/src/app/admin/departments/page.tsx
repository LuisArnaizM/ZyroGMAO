"use client";

import ProtectedPage from "@/components/security/ProtectedPage";
import { ManagementPageLayout } from "@/components/layout/ManagementPageLayout";
import DepartmentPanel from "@/components/layout/DepartmentPanel";

export default function AdminDepartmentsPage() {
  return (
    <ProtectedPage requiredRoles={["Admin", "Supervisor"]}>
      <ManagementPageLayout>
        <div className="flex-1 min-h-0">
          <DepartmentPanel />
        </div>
      </ManagementPageLayout>
    </ProtectedPage>
  );
}
