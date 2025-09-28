"use client";

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ProtectedPage from '@/components/security/ProtectedPage';
import { Card, Empty, Spin, Tree, Tag } from 'antd';
import type { DataNode } from 'antd/es/tree';
import { DepartmentService } from '@/services/department.service';
import { UserService } from '@/services/user.service';
import { Department, UserRead } from '@/types';

function initials(u: UserRead) {
  const a = u.first_name?.[0] || '';
  const b = u.last_name?.[0] || '';
  return (a + b || u.username?.slice(0,2) || '').toUpperCase();
}

export default function DepartmentOrgPage() {
  const params = useParams();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const router = useRouter();
  const depId = Number(params?.id);
  const departmentService = useMemo(() => new DepartmentService(), []);
  const userService = useMemo(() => new UserService(), []);

  const [loading, setLoading] = useState(true);
  const [department, setDepartment] = useState<Department | null>(null);
  const [users, setUsers] = useState<UserRead[]>([]);
  const [allDeps, setAllDeps] = useState<Department[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [deptManager, setDeptManager] = useState<UserRead | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [dep, staff, deps] = await Promise.all([
          departmentService.getById(depId),
          departmentService.getUsers(depId),
          departmentService.getAll(),
        ]);
        // Asegurar que el manager esté incluido aunque no venga en el subtree
        let ensuredStaff = staff;
        let managerUser: UserRead | null = null;
        if (dep?.manager_id) {
          const exists = staff.some(u => u.id === dep.manager_id);
          if (!exists) {
            try {
              const fetched = await userService.getById(dep.manager_id);
              managerUser = fetched;
              ensuredStaff = [...staff, fetched];
            } catch {}
          }
        }
        setDepartment(dep);
        setUsers(ensuredStaff);
        setAllDeps(deps);
        // manager del departamento para cabecera
        const byId = Object.fromEntries(ensuredStaff.map(u => [u.id, u])) as Record<number, UserRead>;
        setDeptManager(dep?.manager_id ? (byId[dep.manager_id] || managerUser || null) : null);
      } finally {
        setLoading(false);
      }
    };
    if (!isNaN(depId)) load();
  }, [depId, departmentService, userService]);

  const treeData: DataNode[] = (() => {
    if (!department) return [];

    const byUserId: Record<number, UserRead> = Object.fromEntries(users.map(u => [u.id, u]));
    const usersByDepId: Record<number, UserRead[]> = users.reduce((acc, u) => {
      const dep = u.department_id;
      if (dep != null) (acc[dep] ||= []).push(u);
      return acc;
    }, {} as Record<number, UserRead[]>);
    const depsByManager: Record<number, Department[]> = {};
    allDeps.forEach(d => {
      if (d.manager_id) (depsByManager[d.manager_id] ||= []).push(d);
    });

    const makeUserTitle = (u: UserRead) => (
      <div className="group flex items-center gap-3 rounded-xl border border-white/10 bg-white/70 dark:bg-neutral-900/50 px-3 py-2 shadow-sm backdrop-blur hover:border-indigo-400/40 transition">
        <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-white grid place-items-center text-xs font-semibold">
          {initials(u)}
        </div>
        <div className="min-w-0">
          <div className="truncate font-medium">{u.first_name} {u.last_name}</div>
          <div className="text-xs text-neutral-500 truncate">{u.email}</div>
        </div>
        <div className="ml-auto">
          <Tag color={u.role === 'Admin' ? 'red' : u.role === 'Supervisor' ? 'blue' : 'green'}>{u.role}</Tag>
        </div>
      </div>
    );

    const buildUserNode = (u: UserRead, visitedDepIds: Set<number>, path: string): DataNode => {
      const managed = (depsByManager[u.id] || []).filter(d => !visitedDepIds.has(d.id));
      const childNodes: DataNode[] = [];
      managed.forEach((d) => {
        const nextVisited = new Set(visitedDepIds);
        nextVisited.add(d.id);
        const dUsers = usersByDepId[d.id] || [];
        const dManager = d.manager_id ? byUserId[d.manager_id] : undefined;
        const dTechs = dUsers.filter(x => (x.role === 'Tecnico' || x.role === 'Supervisor') && (!dManager || x.id !== dManager.id));
        // Nodo grupo del departamento hijo con su nombre visible
        const groupChildren: DataNode[] = [];
        // Evitar duplicar manager: si el manager del dep hijo es el mismo usuario actual (u), no lo añadimos otra vez
        if (dManager && dManager.id !== u.id) {
          groupChildren.push(buildUserNode(dManager, nextVisited, `${path}-dep${d.id}-mgr`));
        }
        dTechs.forEach(t => groupChildren.push(buildUserNode(t, nextVisited, `${path}-dep${d.id}-tech${t.id}`)));
        childNodes.push({
          key: `${path}-dep-${d.id}`,
          title: (
            <div className="px-2 py-1 text-xs rounded-md border border-white/10 bg-white/60 dark:bg-neutral-900/40 inline-flex gap-2 items-center">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
              <span className="font-medium">{d.name}</span>
              <span className="text-[10px] text-neutral-500">Departamento</span>
            </div>
          ),
          children: groupChildren,
        });
      });
      return {
        key: `${path}-u-${u.id}`,
        title: makeUserTitle(u),
        children: childNodes,
      };
    };

    const topVisited = new Set<number>([department.id]);
    const topUsers = usersByDepId[department.id] || [];
    const manager = department.manager_id ? byUserId[department.manager_id] : undefined;
    const techs = topUsers.filter(u => (u.role === 'Tecnico' || u.role === 'Supervisor') && (!manager || u.id !== manager.id));

    // Si hay manager del departamento, mostrarlo como único nodo raíz
    if (manager) {
      const rootMgrNode = buildUserNode(manager, new Set(topVisited), `root-mgr`);
      const techChildren = techs.map(t => buildUserNode(t, new Set(topVisited), `root-tech-${t.id}`));
      return [{
        ...rootMgrNode,
        children: [...techChildren, ...(rootMgrNode.children || [])],
      }];
    }
    // Si no hay manager, mostrar técnicos como raíces
    return techs.map(t => buildUserNode(t, new Set(topVisited), `root-tech-${t.id}`));
  })();

  return (
    <ProtectedPage requiredRoles={["Admin", "Supervisor"]}>
      <div className="p-4 md:p-6 flex flex-col gap-4 h-full">
        <Card className="flex-1 min-h-0 border-white/10 bg-white/50 dark:bg-neutral-900/40 backdrop-blur">
          {loading ? (
            <div className="flex items-center justify-center h-64"><Spin /></div>
          ) : treeData.length ? (
            <Tree
              treeData={treeData}
              defaultExpandAll
              showLine
            />
          ) : (
            <Empty description="Sin datos" />
          )}
        </Card>
      </div>
    </ProtectedPage>
  );
}
