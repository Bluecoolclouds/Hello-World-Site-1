import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Heart,
  MessageCircle,
  Search,
  Shield,
  Users,
  Zap,
  Star,
  Eye,
  Clock,
  ChevronDown,
  Moon,
  Sun,
  Send,
  UserCheck,
  Lock,
  Filter,
} from "lucide-react";
import { SiTelegram } from "react-icons/si";

interface BotStats {
  totalUsers: number;
  totalGirls: number;
  totalMen: number;
  activeChats: number;
  onlineNow: number;
}

function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const stored = localStorage.getItem("theme");
    if (stored === "dark") {
      document.documentElement.classList.add("dark");
      setDark(true);
    }
  }, []);
  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  };
  return (
    <Button
      size="icon"
      variant="ghost"
      onClick={toggle}
      data-testid="button-theme-toggle"
    >
      {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </Button>
  );
}

function AnimatedCounter({ target, label }: { target: number; label: string }) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (target === 0) return;
    const duration = 1200;
    const steps = 40;
    const increment = target / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target]);
  return (
    <div className="text-center">
      <div className="text-3xl font-bold text-primary" data-testid={`text-stat-${label}`}>
        {count}
      </div>
      <div className="text-sm text-muted-foreground mt-1">{label}</div>
    </div>
  );
}

const FEATURES_FOR_MEN = [
  {
    icon: Search,
    title: "Каталог индивидуалок",
    desc: "Реальные фото, параметры, цены — листайте анкеты девушек Астрахани",
  },
  {
    icon: Heart,
    title: "Написать напрямую",
    desc: "Нажмите «Написать» — анонимный чат с девушкой прямо в боте",
  },
  {
    icon: Eye,
    title: "Отслеживание онлайн",
    desc: "Следите за понравившимися — видите кто сейчас на связи",
  },
  {
    icon: MessageCircle,
    title: "Отзывы клиентов",
    desc: "Читайте реальные отзывы и оставляйте свои комментарии",
  },
  {
    icon: Filter,
    title: "Фильтры поиска",
    desc: "Город, возраст, услуги — находите именно то, что нужно",
  },
  {
    icon: Star,
    title: "Подарки",
    desc: "Отправляйте Telegram Stars понравившимся девушкам",
  },
];

const FEATURES_FOR_GIRLS = [
  {
    icon: UserCheck,
    title: "Детальная анкета",
    desc: "Фото, видео, параметры тела, услуги с 70+ опциями из 9 категорий",
  },
  {
    icon: Zap,
    title: "Цены на дом и выезд",
    desc: "Настройте расценки за 1 час, 2 часа и ночь — отдельно для апартаментов и выезда",
  },
  {
    icon: Clock,
    title: "График работы",
    desc: "Автоматический онлайн по расписанию + ручной переключатель",
  },
  {
    icon: MessageCircle,
    title: "Чаты с клиентами",
    desc: "Все сообщения от клиентов приходят прямо в бот, отвечайте мгновенно",
  },
  {
    icon: Users,
    title: "Статистика анкеты",
    desc: "Просмотры, лайки, подписчики, отзывы — отслеживайте популярность",
  },
  {
    icon: Shield,
    title: "Безопасность",
    desc: "Блокировка нежелательных клиентов, полная анонимность",
  },
];

const SERVICE_CATEGORIES = [
  "Секс",
  "Массаж",
  "Стриптиз",
  "Видео звонок",
  "Экстрим",
  "По запросу",
  "Садо-мазо",
  "Разное",
  "Доп",
];

export default function Home() {
  const { data: stats } = useQuery<BotStats>({
    queryKey: ["/api/bot-stats"],
  });

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-[9999] border-b bg-background/80 backdrop-blur-md" role="banner">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-primary fill-primary" />
            <span className="font-bold text-lg">IntimDate</span>
          </div>
          <nav className="hidden md:flex items-center gap-6 text-sm text-muted-foreground" aria-label="Основная навигация">
            <button
              onClick={() => scrollToSection("features")}
              className="hover-elevate"
              data-testid="link-features"
            >
              Возможности
            </button>
            <button
              onClick={() => scrollToSection("how")}
              className="hover-elevate"
              data-testid="link-how"
            >
              Как работает
            </button>
            <button
              onClick={() => scrollToSection("services")}
              className="hover-elevate"
              data-testid="link-services"
            >
              Услуги
            </button>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <a
              href="https://t.me/intimdatebot"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button data-testid="button-open-bot-header">
                <SiTelegram className="w-4 h-4 mr-2" />
                Открыть бот
              </Button>
            </a>
          </div>
        </div>
      </header>

      <main>
      <section className="relative overflow-hidden py-20 md:py-32" aria-label="Главная">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-accent/5 to-transparent" />
        <div className="relative max-w-6xl mx-auto px-4 text-center">
          <Badge variant="secondary" className="mb-6" data-testid="badge-hero">
            <Zap className="w-3 h-3 mr-1" />
            Эскорт услуги Астрахань
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            Девушки по вызову
            <br />
            <span className="text-primary">в Астрахани</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Проверенные индивидуалки с реальными фото, ценами и отзывами клиентов.
            Эскорт на дом и выезд — без предоплаты, прямо в Telegram.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
            <Badge variant="outline" className="text-sm px-3 py-1.5" data-testid="badge-verified">
              <Shield className="w-3.5 h-3.5 mr-1.5 text-primary" />
              Все анкеты проверены
            </Badge>
            <Badge variant="outline" className="text-sm px-3 py-1.5" data-testid="badge-no-prepay">
              <Lock className="w-3.5 h-3.5 mr-1.5 text-primary" />
              Работаем без предоплаты
            </Badge>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="https://t.me/intimdatebot"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="lg" data-testid="button-open-bot-hero">
                <SiTelegram className="w-5 h-5 mr-2" />
                Открыть каталог
              </Button>
            </a>
            <Button
              variant="outline"
              size="lg"
              onClick={() => scrollToSection("features")}
              data-testid="button-learn-more"
            >
              Узнать больше
              <ChevronDown className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {stats && (
        <section className="py-12 border-y bg-muted/30" aria-label="Статистика">
          <div className="max-w-4xl mx-auto px-4 grid grid-cols-3 gap-8">
            <AnimatedCounter
              target={stats.totalUsers + 70}
              label="Клиентов в Астрахани"
            />
            <AnimatedCounter target={stats.totalGirls + 10} label="Проверенных анкет" />
            <AnimatedCounter target={stats.onlineNow} label="Девушек онлайн" />
          </div>
        </section>
      )}

      <section id="features" className="py-20" aria-label="Возможности для клиентов">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-3">Для клиентов</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Найдите девушку по вызову в Астрахани — анонимно, быстро, без предоплаты
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES_FOR_MEN.map((f, i) => (
              <Card key={i} className="hover-elevate" data-testid={`card-feature-men-${i}`}>
                <CardContent className="p-6">
                  <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center mb-4">
                    <f.icon className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-muted/30" aria-label="Возможности для девушек">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-3">Для девушек эскорта</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Полный контроль над профилем, расценками и общением с клиентами
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {FEATURES_FOR_GIRLS.map((f, i) => (
              <Card key={i} className="hover-elevate" data-testid={`card-feature-girls-${i}`}>
                <CardContent className="p-6">
                  <div className="w-10 h-10 rounded-md bg-accent/10 flex items-center justify-center mb-4">
                    <f.icon className="w-5 h-5 text-accent" />
                  </div>
                  <h3 className="font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="how" className="py-20" aria-label="Как это работает">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-3">Как это работает</h2>
          </div>
          <div className="space-y-8">
            {[
              {
                step: "1",
                icon: Send,
                title: "Откройте бот",
                desc: "Нажмите /start в Telegram — регистрация автоматическая",
              },
              {
                step: "2",
                icon: Search,
                title: "Листайте анкеты",
                desc: "Просматривайте профили с фото, ценами и услугами",
              },
              {
                step: "3",
                icon: Heart,
                title: "Напишите",
                desc: "Нажмите «Написать» — создастся чат прямо в боте, анонимно",
              },
              {
                step: "4",
                icon: MessageCircle,
                title: "Общайтесь",
                desc: "Переписывайтесь в чате бота — сообщения доставляются мгновенно",
              },
              {
                step: "5",
                icon: Heart,
                title: "Наслаждайтесь встречей",
                desc: "Договоритесь о деталях и проведите незабываемое время вместе — страсть и удовольствие гарантированы",
              },
            ].map((s, i) => (
              <div
                key={i}
                className="flex items-start gap-5"
                data-testid={`step-${i}`}
              >
                <div className="w-10 h-10 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-bold shrink-0">
                  {s.step}
                </div>
                <div>
                  <h3 className="font-semibold mb-1 flex items-center gap-2">
                    <s.icon className="w-4 h-4 text-muted-foreground" />
                    {s.title}
                  </h3>
                  <p className="text-sm text-muted-foreground">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="services" className="py-20 bg-muted/30" aria-label="Каталог услуг">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold mb-3">Каталог услуг</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              9 категорий с более чем 70 вариантами услуг — девушки выбирают что
              предложить
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {SERVICE_CATEGORIES.map((cat, i) => (
              <Badge
                key={i}
                variant="secondary"
                className="text-sm px-4 py-2"
                data-testid={`badge-service-${i}`}
              >
                {cat}
              </Badge>
            ))}
          </div>
          <div className="mt-10 text-center">
            <Card>
              <CardContent className="p-8">
                <div className="grid grid-cols-3 gap-6 text-center mb-6">
                  <div>
                    <div className="text-2xl font-bold text-primary">1 час</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Короткая встреча
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary">2 часа</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Стандарт
                    </div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-primary">Ночь</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      До утра
                    </div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Каждая девушка устанавливает свои цены — на дому и на выезд
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <section className="py-20" aria-label="Безопасность">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold mb-3">Безопасность</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Lock,
                title: "Анонимность",
                desc: "Ваши данные не видны другим — общение через бот",
              },
              {
                icon: Shield,
                title: "Блокировка",
                desc: "Заблокируйте любого пользователя в один клик",
              },
              {
                icon: UserCheck,
                title: "Модерация",
                desc: "Админ следит за порядком — бан нарушителей",
              },
            ].map((f, i) => (
              <Card key={i} data-testid={`card-security-${i}`}>
                <CardContent className="p-6 text-center">
                  <div className="w-10 h-10 rounded-md bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <f.icon className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="font-semibold mb-2">{f.title}</h3>
                  <p className="text-sm text-muted-foreground">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-primary/10 via-accent/5 to-transparent" aria-label="Призыв к действию">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Эскорт Астрахань — начните сейчас</h2>
          <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
            Откройте бот в Telegram — каталог девушек по вызову с реальными фото и ценами.
            Без регистрации, без предоплаты.
          </p>
          <a
            href="https://t.me/intimdatebot"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Button size="lg" data-testid="button-open-bot-cta">
              <SiTelegram className="w-5 h-5 mr-2" />
              Открыть бот в Telegram
            </Button>
          </a>
        </div>
      </section>
      </main>

      <footer className="py-8 border-t" role="contentinfo">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-primary fill-primary" />
            <span>IntimDate</span>
          </div>
          <p>Эскорт услуги Астрахань — проверенные девушки в Telegram</p>
        </div>
      </footer>
    </div>
  );
}
