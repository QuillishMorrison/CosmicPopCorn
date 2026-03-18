import { Card, SectionTitle, Tooltip } from '../../components/ui'
import { moduleCatalog, moduleCostForLevel } from '../../lib/gameContent'
import { describeResource, labelForResource } from '../../lib/i18n'

const resources = ['credits', 'energy', 'fuel', 'parts', 'data', 'crew', 'alloy', 'insight', 'reputation']

const startingResources = [
  ['credits', 1200],
  ['energy', 30],
  ['fuel', 55],
  ['parts', 40],
  ['data', 30],
  ['crew', 6],
  ['alloy', 24],
  ['insight', 8]
] as const

const startingModules = ['Док I', 'Склад I', 'Реактор I']

const contractTypeDocs = [
  ['Доставка', 'Разовый запрос на точный объём ресурса. Самый прямой тип контракта: привезти и закрыть дефицит.'],
  ['Снабжение', 'Логистический контракт на стабильные поставки. Чаще всего подходит для топлива, деталей и сплава.'],
  ['Данные', 'Контракт на аналитический поток и цифровые пакеты. Сильнее всего раскрывается у дата-специализации.'],
  ['Ремонт', 'Сервисный контракт с упором на детали и ремонтную цепочку.'],
  ['Переработка', 'Контракт на сортировку, переработку и обслуживание производственного потока.']
] as const

const moduleEffects = [
  ['Док', '+5 throughput, +3 к входящему потоку, +1 слот контрактов, -2 энергии'],
  ['Склад', '+2 throughput, +100 хранения, -1 энергия'],
  ['Реактор', '+1 throughput, +15 энергии supply'],
  ['Ремонтный отсек', '+6 throughput, +8 repair capacity, -3 энергии, -1 экипаж'],
  ['Жилой модуль', '+2 throughput, +4 crew capacity, +3 stability, -2 энергии'],
  ['Рыночный терминал', '+4 throughput, +5% trade bonus, -1 энергия'],
  ['Дата-ядро', '+5 throughput, +7 data output, +0.8 insight gain, -2 энергии'],
  ['Узел автоматизации', '+8 throughput, +8% automation, -2 энергии']
] as const

const t = {
  title: 'Гид по сектору',
  subtitle: 'Цифры, логика и краткие правила игры',
  start: 'Старт станции',
  startTip: 'Новая станция создаётся не пустой: у тебя уже есть базовый набор модулей и ресурсов для первых решений.',
  simulation: 'Как считает игра',
  simulationTip: 'Симуляция идёт на сервере пакетными тиками. Сейчас тик мира и обновление станции настроены на 1 секунду.',
  contracts: 'Типы контрактов',
  contractsTip: 'Тип контракта описывает смысл заказа и помогает быстро понять, зачем нужен ресурс.',
  resourcesTitle: 'Ресурсы',
  resourcesTip: 'Каждый ресурс здесь описан с точки зрения реальной пользы для станции.',
  modules: 'Модули и эффекты',
  modulesTip: 'Ниже указаны цена первого уровня и конкретный вклад модуля в экономику станции.',
  formulas: 'Ключевые формулы',
  formulasTip: 'Это упрощённые правила MVP, на которых держится экономика станции.',
  formulasList: [
    'Тик мира: 1 секунда.',
    'Офлайн-прогресс считается максимум за 8 часов за один заход.',
    'Данные на главной обновляются раз в секунду, вместе с новым серверным тиком.',
    'Стартовый throughput: 14 у Freight Hub и 12 у остальных специализаций.',
    'Апгрейд модуля: цена = базовая цена × (1 + 0.45 × (следующий уровень - 1)).',
    'Credits за тик: throughput × 2 × efficiency.',
    'Fuel за тик: 0.7 у Freight Hub, иначе 0.35.',
    'Parts за тик: 0.55 с Repair Bay, иначе 0.25.',
    'Data за тик: 0.2 базово или 0.22 × data output при наличии Data Core.',
    'Alloy за тик: 0.35 со Складом, иначе 0.15.',
    'Insight за тик: insight gain × 0.1, а у Data Exchange ещё ×1.2.',
    'Efficiency зависит от энергии, экипажа, заполненности склада, автоматизации и бонуса специализации.'
  ]
}

export function GuidePage() {
  return (
    <div className="space-y-4">
      <Card>
        <SectionTitle title={t.title} subtitle={t.subtitle} />
      </Card>

      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.startTip}>
              <span>{t.start}</span>
            </Tooltip>
          }
        />
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
            <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">Стартовые модули</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {startingModules.map((module) => (
                <span key={module} className="rounded-full border border-borderSoft px-3 py-1 text-sm text-textMain">
                  {module}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
            <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">Стартовые ресурсы</div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {startingResources.map(([resource, amount]) => (
                <div key={resource} className="rounded-xl border border-borderSoft px-3 py-2 text-sm text-textMain">
                  {labelForResource(resource)}: {amount}
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.formulasTip}>
              <span>{t.formulas}</span>
            </Tooltip>
          }
        />
        <div className="grid gap-3 md:grid-cols-2">
          {t.formulasList.map((line) => (
            <div key={line} className="rounded-2xl border border-borderSoft bg-panelSoft p-4 text-sm leading-relaxed text-textMute">
              {line}
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.resourcesTip}>
              <span>{t.resourcesTitle}</span>
            </Tooltip>
          }
        />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {resources.map((resource) => (
            <div key={resource} className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
              <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">Ресурс</div>
              <div className="mt-1 text-base font-semibold text-textMain">{labelForResource(resource)}</div>
              <p className="mt-2 text-sm leading-relaxed text-textMute">{describeResource(resource)}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.modulesTip}>
              <span>{t.modules}</span>
            </Tooltip>
          }
        />
        <div className="grid gap-3 md:grid-cols-2">
          {moduleCatalog.map((module) => {
            const levelOneCost = moduleCostForLevel(module.buildCost, 1)
            return (
              <div key={module.key} className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
                <div className="text-[10px] uppercase tracking-[0.2em] text-textMute">{module.role}</div>
                <div className="mt-1 text-base font-semibold text-textMain">{module.name}</div>
                <p className="mt-2 text-sm leading-relaxed text-textMute">{module.description}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {levelOneCost.map((cost) => (
                    <span key={cost.resource} className="rounded-full border border-borderSoft px-3 py-1 text-xs text-textMute">
                      {labelForResource(cost.resource)} {cost.amount}
                    </span>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {moduleEffects.map(([name, effect]) => (
            <div key={name} className="rounded-2xl border border-borderSoft bg-panelSoft p-4 text-sm text-textMute">
              <span className="font-semibold text-textMain">{name}:</span> {effect}
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.contractsTip}>
              <span>{t.contracts}</span>
            </Tooltip>
          }
        />
        <div className="grid gap-3 md:grid-cols-2">
          {contractTypeDocs.map(([name, description]) => (
            <div key={name} className="rounded-2xl border border-borderSoft bg-panelSoft p-4">
              <div className="text-base font-semibold text-textMain">{name}</div>
              <div className="mt-2 text-sm leading-relaxed text-textMute">{description}</div>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <SectionTitle
          title={
            <Tooltip label={t.simulationTip}>
              <span>{t.simulation}</span>
            </Tooltip>
          }
        />
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-borderSoft bg-panelSoft p-4 text-sm leading-relaxed text-textMute">
            Энергия, экипаж и склад режут эффективность. Если один из контуров проседает, станция не останавливается,
            но начинает зарабатывать заметно хуже.
          </div>
          <div className="rounded-2xl border border-borderSoft bg-panelSoft p-4 text-sm leading-relaxed text-textMute">
            Хорошее правило ранней игры: держать рынок для дефицита, детали для апгрейдов и хотя бы один модуль,
            который усиливает твою специализацию.
          </div>
        </div>
      </Card>
    </div>
  )
}
