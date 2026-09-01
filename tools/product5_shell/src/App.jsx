import { useEffect, useMemo, useState } from "react";
import QRCode from "qrcode";
import {
  advisorQuestions,
  advisorCopy,
  chapters,
  cityDestinations,
  cityCopy,
  communityStates,
  communityCopy,
  defaultRoute,
  generationMessages,
  livingStandards,
  livingCopy,
  projectProfile,
  routes,
  sceneAssets,
  selectRoute,
} from "./data.js";

const publicBaseUrl = (import.meta.env.VITE_PUBLIC_BASE_URL ?? "").replace(/\/$/, "");
const publicBaseIsSafe =
  /^https:\/\//i.test(publicBaseUrl) &&
  !/(localhost|127\.0\.0\.1|0\.0\.0\.0|\.local)(:\d+)?$/i.test(publicBaseUrl);
const appBasePath = import.meta.env.BASE_URL.endsWith("/")
  ? import.meta.env.BASE_URL
  : `${import.meta.env.BASE_URL}/`;
const withAppBase = (path) => `${appBasePath}${String(path).replace(/^\/+/, "")}`;
const mobileRoutePath = (slug) => `${appBasePath}#/m/${slug}/`;

function useClock() {
  const [time, setTime] = useState(() => new Date());

  useEffect(() => {
    const timer = window.setInterval(() => setTime(new Date()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  return time.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function useScenePreload() {
  const [readyCount, setReadyCount] = useState(0);

  useEffect(() => {
    let live = true;
    let completed = 0;

    sceneAssets.forEach((src) => {
      const image = new Image();
      image.src = withAppBase(src);
      const markReady = () => {
        completed += 1;
        if (live) setReadyCount(completed);
      };

      if (image.decode) {
        image.decode().then(markReady).catch(markReady);
      } else {
        image.onload = markReady;
        image.onerror = markReady;
      }
    });

    return () => {
      live = false;
    };
  }, []);

  return readyCount;
}

function AnimatedNumber({ value, active }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!active) return undefined;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduceMotion) {
      setDisplay(value);
      return undefined;
    }

    const startedAt = performance.now();
    let frame;
    const tick = (now) => {
      const progress = Math.min((now - startedAt) / 780, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(value * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [active, value]);

  return <span>{display}</span>;
}

function SceneBackgrounds({ activeImage }) {
  return (
    <div className="scene-stack" aria-hidden="true">
      {sceneAssets.map((src) => (
        <img
          className={`scene-image ${activeImage === src ? "scene-image--active" : ""}`}
          key={src}
          src={withAppBase(src)}
          alt=""
          decoding="async"
        />
      ))}
      <div className="scene-vignette" />
      <div className="scene-grain" />
    </div>
  );
}

function BrandBar({ readyCount }) {
  const time = useClock();

  return (
    <header className="brand-bar">
      <div className="brand-lockup">
        <p className="brand-name">{projectProfile.name}</p>
        <p className="brand-subtitle">{projectProfile.brand_line}</p>
      </div>
      <div className="system-status" aria-label="当前体验状态">
        <span className={`status-dot ${readyCount === sceneAssets.length ? "status-dot--ready" : ""}`} />
        <span>{readyCount === sceneAssets.length ? "画面已就绪" : "画面准备中"}</span>
        <span className="status-divider" />
        <time>{time}</time>
      </div>
    </header>
  );
}

function SecondaryBand({ hoverId }) {
  const hoveredChapter = chapters.find((chapter) => chapter.id === hoverId);

  return (
    <div className={`secondary-band ${hoveredChapter ? "secondary-band--visible" : ""}`}>
      {hoveredChapter?.secondary.map((item) => (
        <span className="secondary-item" key={item}>
          {item}
        </span>
      ))}
    </div>
  );
}

function PrimaryNav({ activeId, onSelect }) {
  const [hoverId, setHoverId] = useState(null);

  return (
    <div className="navigation-zone" onMouseLeave={() => setHoverId(null)}>
      <SecondaryBand hoverId={hoverId} />
      <nav className="primary-nav" aria-label="体验章节">
        {chapters.map((chapter) => (
          <button
            className={`primary-nav__item ${activeId === chapter.id ? "primary-nav__item--active" : ""}`}
            key={chapter.id}
            type="button"
            onClick={() => onSelect(chapter.id)}
            onMouseEnter={() => setHoverId(chapter.id)}
            onFocus={() => setHoverId(chapter.id)}
            aria-current={activeId === chapter.id ? "page" : undefined}
          >
            <span>{chapter.nav}</span>
            <small>{chapter.navEn}</small>
          </button>
        ))}
      </nav>
    </div>
  );
}

function Eyebrow({ children }) {
  return <p className="eyebrow">{children}</p>;
}

function HomeScene({ onStart }) {
  const home = chapters.find((chapter) => chapter.id === "home");

  return (
    <div className="scene-content scene-content--home">
      <section className="hero-copy scene-enter">
        <Eyebrow>{home.eyebrow}</Eyebrow>
        <h1>{home.title}</h1>
        <p className="hero-summary">{home.summary}</p>
        <button className="button button--primary" type="button" onClick={onStart}>
          开始体验
        </button>
      </section>

      <aside className="glass-panel home-overview scene-enter scene-enter--delay">
        <Eyebrow>三项选择价值</Eyebrow>
        <h2>一处新居，回答三次家庭选择</h2>
        <div className="value-stack">
          {home.values.map((value, index) => (
            <div key={value}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{value}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

function CityScene({ active }) {
  const [selectedId, setSelectedId] = useState(cityDestinations[0].id);
  const selected = cityDestinations.find((item) => item.id === selectedId);

  return (
    <div className="scene-content">
      <section className="glass-panel left-panel scene-enter">
        <Eyebrow>{cityCopy.eyebrow}</Eyebrow>
        <h1>{cityCopy.title}</h1>
        <p className="panel-lead">{cityCopy.lead}</p>
        <div className="mini-proof">
          <strong>{cityCopy.proof_title}</strong>
          <p>{cityCopy.proof_body}</p>
        </div>
      </section>

      <div className="map-markers" aria-label="城市资源点">
        <button
          className="map-marker map-marker--project"
          type="button"
          aria-label={projectProfile.name}
        >
          <span>{cityCopy.project_label}</span>
        </button>
        {cityDestinations.map((item, index) => (
          <button
            className={`map-marker map-marker--position-${index + 1} ${selectedId === item.id ? "map-marker--active" : ""}`}
            key={item.id}
            type="button"
            onClick={() => setSelectedId(item.id)}
          >
            <span>{item.name}</span>
          </button>
        ))}
      </div>

      <aside className="right-rail scene-enter scene-enter--delay">
        <div className="glass-panel destination-focus">
          <Eyebrow>当前目的地</Eyebrow>
          <h2>{selected.name}</h2>
          <div className="destination-value">
            <strong>
              约<AnimatedNumber value={selected.value} active={active} />
              <small>{selected.unit}</small>
            </strong>
            <span>{selected.distance}</span>
          </div>
          <p>{selected.note}</p>
        </div>
        <div className="glass-panel destination-list">
          {cityDestinations.map((item) => (
            <button
              className={selectedId === item.id ? "destination-row destination-row--active" : "destination-row"}
              key={item.id}
              type="button"
              onClick={() => setSelectedId(item.id)}
            >
              <span>{item.name}</span>
              <strong>
                <AnimatedNumber value={item.value} active={active} /> 分钟
              </strong>
            </button>
          ))}
        </div>
      </aside>
    </div>
  );
}

function CommunityScene() {
  const [selectedId, setSelectedId] = useState(communityStates[0].id);
  const selected = communityStates.find((item) => item.id === selectedId);

  return (
    <div className="scene-content">
      <section className="glass-panel left-panel scene-enter">
        <Eyebrow>{communityCopy.eyebrow}</Eyebrow>
        <h1>{communityCopy.title}</h1>
        <p className="panel-lead">{communityCopy.lead}</p>
        <div className="fact-pills" aria-label="已知社区关系">
          {communityCopy.facts.map((fact) => <span key={fact}>{fact}</span>)}
        </div>
      </section>

      <aside className="glass-panel right-panel state-panel scene-enter scene-enter--delay">
        <Eyebrow>空间切换</Eyebrow>
        <div className="segmented-control" aria-label="社区空间切换">
          {communityStates.map((item) => (
            <button
              className={selectedId === item.id ? "segment segment--active" : "segment"}
              key={item.id}
              type="button"
              onClick={() => setSelectedId(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="state-copy" key={selected.id}>
          <h2>{selected.title}</h2>
          <p>{selected.body}</p>
        </div>
        <div className="proof-caption">
          <span>纵向关系</span>
          <span>归家路径</span>
          <span>公共与私密</span>
          <span>时段使用</span>
        </div>
      </aside>
    </div>
  );
}

function LivingScene() {
  const [selectedId, setSelectedId] = useState(livingStandards[0].id);
  const selected = livingStandards.find((item) => item.id === selectedId);

  return (
    <div className="scene-content">
      <section className="glass-panel left-panel scene-enter">
        <Eyebrow>{livingCopy.eyebrow}</Eyebrow>
        <h1>{livingCopy.title}</h1>
        <p className="panel-lead">{livingCopy.lead}</p>
        <div className="mini-proof">
          <strong>{livingCopy.proof_title}</strong>
          <p>{livingCopy.proof_body}</p>
        </div>
      </section>

      <aside className="glass-panel right-panel state-panel scene-enter scene-enter--delay">
        <Eyebrow>六项家庭检验</Eyebrow>
        <div className="standard-grid" aria-label="长期好住标准切换">
          {livingStandards.map((item) => (
            <button
              className={selectedId === item.id ? "standard-button standard-button--active" : "standard-button"}
              key={item.id}
              type="button"
              onClick={() => setSelectedId(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="state-copy" key={selected.id}>
          <h2>{selected.title}</h2>
          <p>{selected.body}</p>
        </div>
      </aside>
    </div>
  );
}

function AdvisorLanding({ onStart }) {
  return (
    <div className="scene-content">
      <section className="glass-panel left-panel advisor-intro scene-enter">
        <Eyebrow>{advisorCopy.eyebrow}</Eyebrow>
        <h1>{advisorCopy.title}</h1>
        <p className="panel-lead">{advisorCopy.lead}</p>
        <button className="button button--primary" type="button" onClick={onStart}>
          开始了解
        </button>
      </section>

      <aside className="glass-panel right-panel advisor-value scene-enter scene-enter--delay">
        <Eyebrow>您将获得</Eyebrow>
        <div className="advisor-benefits">
          {advisorCopy.benefits.map((benefit) => (
            <div key={benefit.title}>
              <strong>{benefit.title}</strong>
              <p>{benefit.body}</p>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

function AdvisorForm({ answers, setAnswers, onGenerate, onExit }) {
  const [questionIndex, setQuestionIndex] = useState(0);
  const question = advisorQuestions[questionIndex];
  const currentAnswer = answers[question.id];
  const hasAnswer = question.multiple
    ? Array.isArray(currentAnswer) && currentAnswer.length > 0
    : Boolean(currentAnswer);

  const choose = (option) => {
    if (!question.multiple) {
      setAnswers((current) => ({ ...current, [question.id]: option }));
      return;
    }

    setAnswers((current) => {
      const selected = current[question.id] ?? [];
      if (selected.includes(option)) {
        return { ...current, [question.id]: selected.filter((item) => item !== option) };
      }
      if (selected.length >= question.max) return current;
      return { ...current, [question.id]: [...selected, option] };
    });
  };

  const next = () => {
    if (!hasAnswer) return;
    if (questionIndex === advisorQuestions.length - 1) {
      onGenerate();
      return;
    }
    setQuestionIndex((current) => current + 1);
  };

  return (
    <div className="scene-content scene-content--form">
      <section className="glass-panel advisor-form scene-enter">
        <div className="form-progress" aria-label={`第${questionIndex + 1}题，共${advisorQuestions.length}题`}>
          <span>了解您的生活</span>
          <strong>
            {String(questionIndex + 1).padStart(2, "0")} / {String(advisorQuestions.length).padStart(2, "0")}
          </strong>
          <div>
            <i className={`form-progress__bar form-progress__bar--${questionIndex + 1}`} />
          </div>
        </div>
        <div className="question-copy" key={question.id}>
          <Eyebrow>{question.help}</Eyebrow>
          <h1>{question.title}</h1>
          <div className="option-grid">
            {question.options.map((option) => {
              const selected = question.multiple
                ? (currentAnswer ?? []).includes(option)
                : currentAnswer === option;
              return (
                <button
                  className={selected ? "choice choice--selected" : "choice"}
                  key={option}
                  type="button"
                  onClick={() => choose(option)}
                  aria-pressed={selected}
                >
                  {option}
                </button>
              );
            })}
          </div>
        </div>
        <div className="form-actions">
          <button
            className="button button--quiet"
            type="button"
            onClick={() => (questionIndex === 0 ? onExit() : setQuestionIndex((current) => current - 1))}
          >
            {questionIndex === 0 ? "返回" : "上一步"}
          </button>
          <button className="button button--primary" type="button" onClick={next} disabled={!hasAnswer}>
            {questionIndex === advisorQuestions.length - 1 ? "生成专属建议" : "下一步"}
          </button>
        </div>
      </section>

      <aside className="glass-panel form-summary scene-enter scene-enter--delay">
        <Eyebrow>已了解</Eyebrow>
        <div className="answer-summary">
          {advisorQuestions.map((item) => {
            const value = answers[item.id];
            return (
              <div key={item.id}>
                <span>{item.title.replace("？", "")}</span>
                <strong>
                  {Array.isArray(value) ? value.join(" · ") : value || "等待您的选择"}
                </strong>
              </div>
            );
          })}
        </div>
      </aside>
    </div>
  );
}

function AdvisorGenerating({ step }) {
  return (
    <div className="generating-wrap">
      <div className="glass-panel generating-card">
        <div className="generation-orbit" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <Eyebrow>正在为您准备</Eyebrow>
        <h1>{generationMessages[step]}</h1>
        <div className="generation-steps">
          {generationMessages.map((message, index) => (
            <div className={index <= step ? "generation-step generation-step--active" : "generation-step"} key={message}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{message}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ResultBlock({ number, title, children }) {
  return (
    <section className="result-block">
      <div className="result-block__heading">
        <span>{number}</span>
        <h3>{title}</h3>
      </div>
      {children}
    </section>
  );
}

function QRContinuation({ route }) {
  const [dataUrl, setDataUrl] = useState("");

  useEffect(() => {
    if (!publicBaseIsSafe) return;
    const url = `${publicBaseUrl}/#/m/${route.slug}/`;
    QRCode.toDataURL(url, {
      width: 260,
      margin: 1,
      color: { dark: "#11271f", light: "#f5f1e8" },
      errorCorrectionLevel: "M",
    }).then(setDataUrl);
  }, [route]);

  if (!publicBaseIsSafe || !dataUrl) return null;

  return (
    <div className="qr-card">
      <img src={dataUrl} alt="手机继续阅读二维码" />
      <div>
        <strong>手机继续看</strong>
        <p>扫描后带走同一组看房建议</p>
        <a href={`${publicBaseUrl}/#/m/${route.slug}/`}>{publicBaseUrl}/#/m/{route.slug}/</a>
      </div>
    </div>
  );
}

function AdvisorResult({ route, onRestart }) {
  const [actionDone, setActionDone] = useState(false);

  return (
    <div className="scene-content scene-content--result">
      <section className="glass-panel result-lead scene-enter">
        <Eyebrow>本次看房建议</Eyebrow>
        <h1>{route.lead}</h1>
        <p>{route.keep}</p>
        <div className="result-focus-tags">
          {advisorCopy.result_tags.map((tag) => <span key={tag}>{tag}</span>)}
        </div>
        <button className="button button--quiet" type="button" onClick={onRestart}>
          重新了解家庭
        </button>
      </section>

      <aside className="glass-panel result-scroll scene-enter scene-enter--delay" tabIndex="0">
        <div className="result-scroll__intro">
          <Eyebrow>您的专属路径</Eyebrow>
          <h2>先得结论，再按顺序把每一项看清</h2>
        </div>

        <ResultBlock number="01" title="您最值得保留的生活">
          <p className="result-paragraph">{route.keep}</p>
        </ResultBlock>

        <ResultBlock number="02" title={`${projectProfile.name}值得重点看的三件事`}>
          <div className="reason-list">
            {route.reasons.map((reason, index) => (
              <article key={reason.title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h4>{reason.title}</h4>
                  <p>{reason.body}</p>
                </div>
              </article>
            ))}
          </div>
        </ResultBlock>

        <ResultBlock number="03" title="建议这样看">
          <ol className="visit-list">
            {route.visit.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </ResultBlock>

        <ResultBlock number="04" title="比较其他项目时请核对">
          <ul className="compare-list">
            {route.compare.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </ResultBlock>

        <ResultBlock number="05" title="下一步安排">
          <div className="next-action">
            <p>{route.next}</p>
            <button className="button button--primary" type="button" onClick={() => setActionDone(true)}>
              加入本次看房安排
            </button>
            {actionDone && <span className="inline-confirmation">已加入，现场可按此顺序继续体验</span>}
          </div>
        </ResultBlock>

        <div className="mobile-continuation">
          <Eyebrow>手机继续阅读</Eyebrow>
          <h3>把同一组建议带到看房现场</h3>
          <p>手机页保留完整的重点、顺序、比较条件与下一步安排。</p>
          <a className="button button--light" href={mobileRoutePath(route.slug)} target="_blank" rel="noreferrer">
            打开手机页
          </a>
          <QRContinuation route={route} />
        </div>
      </aside>
    </div>
  );
}

function AdvisorScene({ phase, setPhase, answers, setAnswers, route, setRoute }) {
  const [generationStep, setGenerationStep] = useState(0);

  useEffect(() => {
    if (phase !== "generating") return undefined;

    setGenerationStep(0);
    const stepTwo = window.setTimeout(() => setGenerationStep(1), 760);
    const stepThree = window.setTimeout(() => setGenerationStep(2), 1540);
    const finish = window.setTimeout(() => setPhase("result"), 2300);

    return () => {
      window.clearTimeout(stepTwo);
      window.clearTimeout(stepThree);
      window.clearTimeout(finish);
    };
  }, [phase, setPhase]);

  const generate = () => {
    setRoute(selectRoute(answers));
    setPhase("generating");
  };

  if (phase === "landing") return <AdvisorLanding onStart={() => setPhase("form")} />;
  if (phase === "form") {
    return (
      <AdvisorForm
        answers={answers}
        setAnswers={setAnswers}
        onGenerate={generate}
        onExit={() => setPhase("landing")}
      />
    );
  }
  if (phase === "generating") return <AdvisorGenerating step={generationStep} />;
  return (
    <AdvisorResult
      route={route}
      onRestart={() => {
        setAnswers({});
        setPhase("form");
      }}
    />
  );
}

function DesktopPrototype() {
  const [activeId, setActiveId] = useState("home");
  const [advisorPhase, setAdvisorPhase] = useState("landing");
  const [answers, setAnswers] = useState({});
  const [route, setRoute] = useState(defaultRoute);
  const readyCount = useScenePreload();

  const chapter = chapters.find((item) => item.id === activeId);
  const activeImage =
    activeId === "advisor" && advisorPhase === "result" ? route.image : chapter.image;

  const selectChapter = (id) => {
    setActiveId(id);
    if (id !== "advisor") window.history.replaceState({}, "", appBasePath);
  };

  return (
    <main className="prototype-shell">
      <SceneBackgrounds activeImage={activeImage} />
      <BrandBar readyCount={readyCount} />

      {activeId === "home" && <HomeScene onStart={() => setActiveId("city")} />}
      {activeId === "city" && <CityScene active />}
      {activeId === "community" && <CommunityScene />}
      {activeId === "living" && <LivingScene />}
      {activeId === "advisor" && (
        <AdvisorScene
          phase={advisorPhase}
          setPhase={setAdvisorPhase}
          answers={answers}
          setAnswers={setAnswers}
          route={route}
          setRoute={setRoute}
        />
      )}

      <PrimaryNav activeId={activeId} onSelect={selectChapter} />
      <p className="prototype-caption">{projectProfile.system_caption}</p>
    </main>
  );
}

function MobileBlock({ number, title, children }) {
  return (
    <section className="mobile-section">
      <div className="mobile-section__heading">
        <span>{number}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function MobileRoutePage({ route }) {
  const [confirmed, setConfirmed] = useState(false);

  return (
    <main className="mobile-route">
      <header className="mobile-hero">
        <img src={withAppBase(route.image)} alt="家庭生活场景" />
        <div className="mobile-hero__overlay" />
        <div className="mobile-brand">
          <span>{projectProfile.name}</span>
          <small>专属看房建议</small>
        </div>
        <div className="mobile-hero__copy">
          <Eyebrow>本次置业判断</Eyebrow>
          <h1>{route.lead}</h1>
        </div>
      </header>

      <div className="mobile-content">
        <MobileBlock number="01" title="您最值得保留的生活">
          <p>{route.keep}</p>
        </MobileBlock>

        <MobileBlock number="02" title={`${projectProfile.name}值得重点看的三件事`}>
          <div className="mobile-reasons">
            {route.reasons.map((reason, index) => (
              <article key={reason.title}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{reason.title}</h3>
                  <p>{reason.body}</p>
                </div>
              </article>
            ))}
          </div>
        </MobileBlock>

        <MobileBlock number="03" title="建议这样看">
          <ol className="mobile-visit">
            {route.visit.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </MobileBlock>

        <MobileBlock number="04" title="比较其他项目时请核对">
          <ul className="mobile-compare">
            {route.compare.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </MobileBlock>

        <MobileBlock number="05" title="下一步安排">
          <div className="mobile-next">
            <p>{route.next}</p>
            <button className="button button--primary" type="button" onClick={() => setConfirmed(true)}>
              保存本次看房安排
            </button>
            {confirmed && <span>已保存，现场可按此顺序继续体验</span>}
          </div>
        </MobileBlock>

        <footer className="mobile-footer">
          <strong>{projectProfile.brand_line}</strong>
          <p>{projectProfile.footer_line}</p>
        </footer>
      </div>
    </main>
  );
}

function resolveMobileRoute() {
  const match = window.location.hash.match(/^#\/m\/([^/]+)\/?$/);
  if (!match && /\/m\/index\.html$/.test(window.location.pathname)) return defaultRoute;
  if (!match) return null;
  return routes[match[1]] ?? defaultRoute;
}

export function App() {
  const mobileRoute = useMemo(resolveMobileRoute, []);
  return mobileRoute ? <MobileRoutePage route={mobileRoute} /> : <DesktopPrototype />;
}
