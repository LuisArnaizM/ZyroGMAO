"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { 
  MdDashboard, 
  MdBuild, 
  MdAssignment, 
  MdInventory, 
  MdTrendingUp,
  MdSpeed,
  MdSecurity,
  MdNotifications,
  MdArrowForward,
  MdCheck,
  MdAnalytics,
  MdWarning
} from "react-icons/md";

export default function Home() {
  const [authed, setAuthed] = useState<boolean>(false);
  useEffect(() => {
    // Home pública: detectar si hay token para ajustar CTAs
    if (typeof window !== 'undefined') {
      const has = !!localStorage.getItem('access_token');
      setAuthed(has);
    }
  }, []);
  const features = [
    {
      icon: <MdSpeed className="w-8 h-8" />,
      title: "Eficiencia Operativa",
      description: "Optimiza procesos de mantenimiento y reduce tiempos de inactividad con IA predictiva",
      gradient: "from-indigo-500/20 to-purple-500/20"
    },
    {
      icon: <MdSecurity className="w-8 h-8" />,
      title: "Control Total",
      description: "Seguimiento completo de equipos, órdenes y recursos en tiempo real con dashboards inteligentes",
      gradient: "from-emerald-500/20 to-teal-500/20"
    },
    {
      icon: <MdTrendingUp className="w-8 h-8" />,
      title: "Análisis Avanzado",
      description: "Reportes y métricas para tomar decisiones informadas basadas en datos históricos",
      gradient: "from-violet-500/20 to-purple-500/20"
    },
    {
      icon: <MdNotifications className="w-8 h-8" />,
      title: "Alertas Inteligentes",
      description: "Notificaciones proactivas para mantenimiento preventivo con machine learning",
      gradient: "from-orange-500/20 to-red-500/20"
    }
  ];

  const quickActions = [
    {
      href: authed ? "/dashboard" : "/login?redirect=/dashboard",
      icon: <MdDashboard className="w-6 h-6" />,
      title: "Dashboard",
      description: "Vista general del sistema",
      stats: "8 widgets activos"
    },
    {
      href: authed ? "/assets" : "/login?redirect=/assets",
      icon: <MdInventory className="w-6 h-6" />,
      title: "Assets",
      description: "Gestión de activos",
      stats: "150+ equipos"
    },
    {
      href: authed ? "/workorders" : "/login?redirect=/workorders",
      icon: <MdAssignment className="w-6 h-6" />,
      title: "Órdenes",
      description: "Órdenes de trabajo",
      stats: "23 pendientes"
    },
    {
      href: authed ? "/maintenance" : "/login?redirect=/maintenance",
      icon: <MdBuild className="w-6 h-6" />,
      title: "Mantenimiento",
      description: "Programación y control",
      stats: "5 programadas"
    }
  ];

  const stats = [
    { number: "150+", label: "Assets Monitoreados", trend: "+12%" },
    { number: "98.5%", label: "Tiempo Operativo", trend: "+2.1%" },
    { number: "24/7", label: "Monitoreo Continuo", trend: "100%" },
    { number: "45", label: "Alertas Resueltas", trend: "+8%" }
  ];

  const recentActivities = [
    { type: "success", message: "Mantenimiento preventivo completado", time: "Hace 2 horas", icon: <MdCheck /> },
    { type: "warning", message: "Alerta de temperatura en Equipo #42", time: "Hace 4 horas", icon: <MdWarning /> },
    { type: "info", message: "Nueva orden de trabajo asignada", time: "Hace 6 horas", icon: <MdAssignment /> },
  ];

  return (
    <div className="min-h-full bg-gradient-to-br from-background via-header-start to-primary-50">
      {/* Hero Section con diseño moderno */}
      <section className="relative py-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header decorativo */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center px-6 py-3 rounded-full primary-gradient border border-white/20 text-indigo-700 dark:text-indigo-300 text-sm font-semibold mb-8 backdrop-blur-sm">
              <MdCheck className="w-5 h-5 mr-2" />
              Sistema GMAO de Nueva Generación
            </div>

            <h1 className="text-6xl md:text-7xl font-bold text-foreground mb-8 leading-tight">  
              <span className="primary-gradient bg-clip-text ">
                Zyro GMAO
              </span>
            </h1>

            <p className="text-xl text-muted mb-12 max-w-4xl mx-auto leading-relaxed">
              Revoluciona la gestión de mantenimiento industrial con tecnología de vanguardia. 
              IA predictiva, análisis en tiempo real y control total de tus operaciones.
            </p>

            {/* CTAs principales */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center mb-20">
      <Link href={authed ? "/dashboard" : "/login?redirect=/dashboard"} className="group">
                <div className="primary-gradient px-10 py-5 rounded-2xl font-semibold text-indigo-700 dark:text-indigo-300 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl border border-white/20 backdrop-blur-sm">
                  <span className="flex items-center justify-center">
                    <MdDashboard className="mr-3 w-6 h-6" />
        {authed ? 'Acceder al Dashboard' : 'Iniciar sesión para acceder'}
                    <MdArrowForward className="ml-3 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </span>
                </div>
              </Link>
              
      <Link href={authed ? "/assets" : "/login?redirect=/assets"} className="group">
                <div className="px-10 py-5 rounded-2xl font-semibold text-foreground transition-all duration-300 bg-white/70 dark:bg-neutral-800/50 border border-neutral-200/70 dark:border-neutral-700 hover:bg-white dark:hover:bg-neutral-800 backdrop-blur-sm">
                  <span className="flex items-center justify-center">
                    <MdInventory className="mr-3 w-6 h-6" />
        {authed ? 'Explorar Assets' : 'Inicia sesión para explorar'}
                  </span>
                </div>
              </Link>
            </div>

            {/* Stats mejoradas */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {stats.map((stat, index) => (
                <div key={index} className="relative group">
                  <div className="elegant-card p-6 hover:scale-105">
                    <div className="text-4xl md:text-5xl font-bold text-foreground mb-2">
                      {stat.number}
                    </div>
                    <div className="text-sm text-muted font-medium mb-1">
                      {stat.label}
                    </div>
                    <div className="text-xs text-primary font-semibold">
                      {stat.trend}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Elementos decorativos con gradientes */}
        <div className="absolute top-20 left-10 w-32 h-32 primary-gradient rounded-full opacity-20 animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-40 h-40 secondary-gradient rounded-full opacity-30 animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 header-gradient rounded-full opacity-10 animate-pulse delay-500"></div>
      </section>

      {/* Quick Actions rediseñadas */}
      <section className="px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
              Acceso Directo
            </h2>
            <p className="text-muted text-xl max-w-3xl mx-auto">
              Navega a las funcionalidades principales con un solo clic
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {quickActions.map((action, index) => (
              <Link key={index} href={action.href} className="group">
                <div className="elegant-card p-8 hover:scale-105 hover:shadow-2xl relative overflow-hidden">
                  <div className="absolute inset-0 primary-gradient opacity-0 group-hover:opacity-10 transition-opacity duration-500"></div>
                  
                  <div className="relative z-10">
                    <div className="primary-gradient w-16 h-16 rounded-2xl flex items-center justify-center text-indigo-700 dark:text-indigo-300 mb-6 group-hover:scale-110 transition-transform duration-300">
                      {action.icon}
                    </div>
                    
                    <h3 className="text-2xl font-bold text-foreground mb-3">
                      {action.title}
                    </h3>
                    
                    <p className="text-muted mb-4 leading-relaxed">
                      {action.description}
                    </p>
                    
                    <div className="text-sm text-primary font-semibold mb-4">
                      {action.stats}
                    </div>
                    
                    <div className="flex items-center text-primary font-semibold group-hover:text-indigo-600 transition-colors">
                      Acceder
                      <MdArrowForward className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section rediseñada */}
      <section className="px-6 py-20 header-gradient">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
              Tecnología de Vanguardia
            </h2>
            <p className="text-muted text-xl max-w-3xl mx-auto">
              Características diseñadas para maximizar la eficiencia industrial
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {features.map((feature, index) => (
              <div key={index} className="group">
                <div className="elegant-card p-10 hover:scale-105 hover:shadow-2xl">
                  <div className={`w-20 h-20 bg-gradient-to-r ${feature.gradient} rounded-2xl flex items-center justify-center text-foreground mb-8 group-hover:scale-110 transition-transform duration-300`}>
                    {feature.icon}
                  </div>
                  
                  <h3 className="text-2xl font-bold text-foreground mb-4">
                    {feature.title}
                  </h3>
                  
                  <p className="text-muted leading-relaxed text-lg">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Actividad Reciente */}
      <section className="px-6 py-20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-6">
              Actividad Reciente
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {recentActivities.map((activity, index) => (
              <div key={index} className="elegant-card p-6 hover:scale-105 transition-all duration-300">
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    activity.type === 'success' ? 'bg-emerald-500/20 text-emerald-600' :
                    activity.type === 'warning' ? 'bg-orange-500/20 text-orange-600' :
                    'bg-indigo-500/20 text-indigo-600'
                  }`}>
                    {activity.icon}
                  </div>
                  <div className="flex-1">
                    <p className="text-foreground font-medium mb-1">{activity.message}</p>
                    <p className="text-muted text-sm">{activity.time}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Final */}
      <section className="px-6 py-20 primary-gradient relative overflow-hidden">
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-5xl font-bold text-indigo-700 dark:text-indigo-300 mb-6">
            Transforma tu Operación
          </h2>
          <p className="text-indigo-600 dark:text-indigo-400 text-xl mb-12 max-w-3xl mx-auto leading-relaxed">
            Únete a la revolución del mantenimiento industrial inteligente con Zyro GMAO
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
    <Link href={authed ? "/dashboard" : "/login?redirect=/dashboard"} className="group">
              <div className="px-10 py-5 bg-white text-indigo-600 rounded-2xl font-bold hover:bg-indigo-50 transition-all duration-300 shadow-lg hover:shadow-xl">
                <span className="flex items-center justify-center">
                  <MdAnalytics className="mr-3 w-6 h-6" />
      {authed ? 'Ir al Dashboard' : 'Iniciar sesión'}
                  <MdArrowForward className="ml-3 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </span>
              </div>
            </Link>
          </div>
        </div>
        
        {/* Elementos decorativos */}
        <div className="absolute top-10 left-10 w-20 h-20 bg-white/10 rounded-full animate-pulse"></div>
        <div className="absolute bottom-10 right-10 w-32 h-32 bg-white/10 rounded-full animate-pulse delay-1000"></div>
      </section>
    </div>
  );
}