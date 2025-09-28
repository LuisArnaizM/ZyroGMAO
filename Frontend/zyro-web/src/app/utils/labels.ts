// Utilidades para colores y etiquetas legibles
export const formatLabel = (v?: string | null) => {
  if (!v) return '';
  // normalizar: aceptar 'IN_PROGRESS', 'in_progress', 'In Progress' -> 'In progress'
  const s = String(v).replace(/_/g, ' ').toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
};

export const getWorkOrderStatusColor = (v?: string | null) => {
  switch ((v || '').toString().toUpperCase()) {
    case 'OPEN':
      return 'blue';
    case 'ASSIGNED':
      return 'orange';
    case 'IN_PROGRESS':
      return 'yellow';
    case 'COMPLETED':
      return 'green';
    case 'CANCELLED':
      return 'red';
    default:
      return 'default';
  }
};

export const getWorkOrderTypeColor = (v?: string | null) => {
  switch ((v || '').toString().toUpperCase()) {
    case 'REPAIR':
      return 'red';
    case 'INSPECTION':
      return 'blue';
    case 'MAINTENANCE':
      return 'purple';
    default:
      return 'default';
  }
};

export const getFailureStatusColor = (v?: string | null) => {
  switch ((v || '').toString().toLowerCase()) {
    case 'pending':
      return 'orange';
    case 'in_progress':
    case 'in progress':
      return 'blue';
    case 'resolved':
      return 'green';
    case 'cancelled':
      return 'red';
    default:
      return 'default';
  }
};

export const getTaskStatusColor = (v?: string | null) => {
  switch ((v || '').toString().toLowerCase()) {
    case 'pending':
      return 'orange';
    case 'in_progress':
    case 'in progress':
      return 'blue';
    case 'completed':
      return 'green';
    case 'cancelled':
      return 'red';
    default:
      return 'default';
  }
};

export const getWorkOrderPriorityColor = (v?: string | null) => {
  switch ((v || '').toString().toUpperCase()) {
    case 'LOW':
      return 'green';
    case 'MEDIUM':
      return 'orange';
    case 'HIGH':
      return 'red';
    default:
      return 'default';
  }
};

export const getSeverityColor = (v?: string | null) => {
  switch ((v || '').toString().toLowerCase()) {
    case 'low':
      return 'green';
    case 'medium':
      return 'orange';
    case 'high':
      return 'red';
    case 'critical':
      return 'magenta';
    default:
      return 'default';
  }
};

export const getMaintenanceStatusColor = (v?: string | null) => {
  switch ((v || '').toString().toLowerCase()) {
    case 'scheduled':
      return 'orange';
    case 'in_progress':
    case 'in progress':
      return 'blue';
    case 'completed':
      return 'green';
    case 'cancelled':
      return 'red';
    default:
      return 'default';
  }
};

export const getAssetStatusColor = (v?: string | null) => {
  switch ((v || '').toString().toLowerCase()) {
    case 'active':
      return 'green';
    case 'inactive':
      return 'red';
    case 'maintenance':
      return 'orange';
    case 'retired':
      return 'gray';
    default:
      return 'default';
  }
};

export const getComponentStatusColor = getAssetStatusColor;

