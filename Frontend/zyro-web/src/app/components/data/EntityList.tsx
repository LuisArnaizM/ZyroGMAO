"use client";
import React, { useEffect, useState } from "react";
import { Popconfirm, Space, Tooltip } from "antd";
import { Table, Tooltip as AntTooltip } from "antd";
import type { ColumnsType, ColumnType } from "antd/es/table";
import { ListCard } from "../layout/ListCard";
import { PlusCircleOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from "@ant-design/icons";
import { AppButton } from "../ui/AppButton";

export type KeyGetter<T> = keyof T | ((record: T) => React.Key);

export type PaginationState = {
  current: number;
  pageSize: number;
  total?: number;
};

export type EntityListProps<T extends object> = {
  icon?: React.ReactNode;
  title: string;
  data: T[];
  columns: ColumnsType<T>;
  rowKey: KeyGetter<T>;
  loading?: boolean;
  createLabel?: string;
  onCreate?: () => void;
  onView?: (record: T) => void;
  // Handler for explicit double click (overrides default onView double click)
  onDoubleClick?: (record: T) => void;
  onEdit?: (record: T) => void;
  onDelete?: (record: T) => void | Promise<void>;
  // Puede ser un nodo estático o una función que recibe la fila seleccionada
  headerExtras?: React.ReactNode | ((selected: T | null) => React.ReactNode);
  scrollX?: number | string;
  scrollY?: number | string;
  // Evita que el contenido de las celdas se parta en varias líneas
  nowrap?: boolean;
  viewButtonLabel?: string;
  // Paginación controlada (server-side). Si no se pasa, usa paginación por defecto client-side.
  pagination?: PaginationState;
  onChangePage?: (page: number, pageSize: number) => void;
};

export function EntityList<T extends object>(props: EntityListProps<T>) {
  const {
    icon,
    title,
    data,
    columns,
    rowKey,
    loading,
    createLabel = "Add ",
    onCreate,
    onView,
    onEdit,
    onDelete,
    headerExtras,
    scrollX = 'max-content',
    scrollY,
    nowrap = true,
    pagination,
    onChangePage,
    onDoubleClick,
  } = props;

  const [selectedRow, setSelectedRow] = useState<T | null>(null);

  // Mantener selección válida si cambia data
  useEffect(() => {
    if (!selectedRow) return;
    const key = getKey(selectedRow);
    if (!data.some((r) => getKey(r) === key)) {
      setSelectedRow(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const getKey = (record: T): React.Key => {
    if (typeof rowKey === "function") return rowKey(record);
    return record[rowKey] as React.Key;
  };
  const extras = typeof headerExtras === "function" ? headerExtras(selectedRow) : headerExtras;

  // Enriquecer columnas: si no tienen render propio añadimos ellipsis + tooltip (title / Tooltip)
  const enhancedColumns: ColumnsType<T> = (columns as ColumnsType<T>).map((col: ColumnType<T>) => {
    if (col.render) return col;
    const dataIndex = col.dataIndex as string | number | undefined;
    if (dataIndex === undefined) return col;
    return {
      ...col,
      ellipsis: true,
      render: (value: unknown) => {
        if (value === null || value === undefined) return value as React.ReactNode;
        const str = typeof value === 'string' ? value : String(value);
        if (str.length > 15) {
          return (
            <AntTooltip placement="top" title={str} arrow>
              <span className="inline-block max-w-[220px] truncate align-middle">{str}</span>
            </AntTooltip>
          );
        }
        return <span title={str}>{str}</span>;
      },
    } as ColumnType<T>;
  });

  return (
    <div className="relative h-full">
      {/* Card principal con contenido */}
      <ListCard
        title=""
        action={
          onCreate && (
            <AppButton variant="primary" icon={<PlusCircleOutlined />} onClick={onCreate}>
              {createLabel}
            </AppButton>
          )
        }
        actions={
          <Space>
            <Tooltip title="View Details">
              <span>
                <AppButton
                  variant="primary"
                  icon={<SearchOutlined />}
                  disabled={!selectedRow}
                  onClick={() => selectedRow && onView && onView(selectedRow)}
                >
                </AppButton>
              </span>
            </Tooltip>
            {onEdit && (
              <Tooltip title="Edit">
                <span>
                  <AppButton
                    variant="secondary"
                    icon={<EditOutlined />}
                    disabled={!selectedRow}
                    onClick={() => selectedRow && onEdit(selectedRow)}
                  />
                </span>
              </Tooltip>
            )}
            {onDelete && (
              <Popconfirm
                title="Are you sure you want to delete this item?"
                onConfirm={() => selectedRow && onDelete(selectedRow)}
                okText="Yes"
                cancelText="No"
                disabled={!selectedRow}
              >
                <Tooltip title="Delete">
                  <span>
                    <AppButton variant="danger" icon={<DeleteOutlined />} disabled={!selectedRow} />
                  </span>
                </Tooltip>
              </Popconfirm>
            )}
            {extras}
          </Space>
        }
      >
      
      {/* Título superpuesto a la altura de los botones - sin ocupar espacio */}
      <div className="absolute top-4 left-6 z-20">
        <div className="primary-gradient-dark rounded-xl text-primary px-4 py-2 shadow-lg">
          <div className="flex items-center gap-2">
            {icon && <span className="text-lg">{icon}</span>}
            <h2 className="text-primary font-bold m-0 whitespace-nowrap">
              {title}
            </h2>
          </div>
        </div>
      </div>
      {/* Contenedor que ocupa el 100% y gestiona el scroll vertical */}
    <div className="flex-1 min-h-0" style={scrollY ? { maxHeight: scrollY } : undefined}>
        <Table<T>
          columns={enhancedColumns}
          dataSource={data}
          rowKey={rowKey as unknown as string}
          className={`${nowrap ? 'whitespace-nowrap' : ''} elegant-table`}
          loading={loading}
          onRow={(record) => ({
            onClick: () => setSelectedRow(record),
            onDoubleClick: () => (onDoubleClick ? onDoubleClick(record) : onView && onView(record)),
            className: selectedRow && getKey(selectedRow) === getKey(record) 
              ? 'selected-row' 
              : 'selectable-row',
          })}
          pagination={
            pagination
              ? {
                  current: pagination.current,
                  pageSize: pagination.pageSize,
                  total: pagination.total ?? data.length,
                  hideOnSinglePage: false,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
                  onChange: (page, pageSize) => onChangePage && onChangePage(page, pageSize || pagination.pageSize),
                  onShowSizeChange: (_current, size) => onChangePage && onChangePage(1, size),
                }
              : {
                  total: data.length,
                  hideOnSinglePage: false,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
                }
          }
          scroll={{ x: scrollX ? scrollX : 'max-content', y: scrollY ? scrollY : 'calc(100vh - 425px)' }}

        />
      </div>
    </ListCard>
    </div>
  );
}
