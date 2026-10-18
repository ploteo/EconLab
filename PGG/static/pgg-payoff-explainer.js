(() => {
  const formatNumber = (value, locale) => {
    const rounded = Math.round(value * 100) / 100;
    return new Intl.NumberFormat(locale, {
      maximumFractionDigits: 2,
    }).format(rounded);
  };

  const initialiseExplainers = () => document.querySelectorAll('.pgg-payoff-explainer').forEach(explainer => {
    const endowment = Number(explainer.dataset.endowment);
    const multiplier = Number(explainer.dataset.multiplier);
    const players = Number(explainer.dataset.players);
    const locale = explainer.dataset.locale === 'it' ? 'it-IT' : 'en';
    const pointsUnit = explainer.dataset.pointsUnit || (explainer.dataset.locale === 'it' ? 'punti' : 'points');
    const inputs = Array.from(explainer.querySelectorAll('[data-contribution]'));
    const outputs = Array.from(explainer.querySelectorAll('[data-output]'));

    if (!Number.isFinite(endowment) || !Number.isFinite(multiplier) || !Number.isFinite(players)) {
      return;
    }

    const exampleContribution = Math.round(endowment / 2);
    inputs.forEach(input => {
      input.value = exampleContribution;
    });

    const setValue = (name, value) => {
      explainer.querySelectorAll(`[data-value="${name}"]`).forEach(element => {
        element.textContent = formatNumber(value, locale);
      });
    };

    const update = () => {
      const contributions = inputs.map(input => Number(input.value));
      const totalContribution = contributions.reduce((total, value) => total + value, 0);
      const projectReturn = totalContribution * multiplier;
      const individualShare = projectReturn / players;
      const amountKept = endowment - contributions[0];
      const payoff = amountKept + individualShare;

      contributions.forEach((value, index) => {
        outputs[index].textContent = `${formatNumber(value, locale)} ${pointsUnit}`;
        inputs[index].style.setProperty('--pgg-fill', `${(value / endowment) * 100}%`);
        const bar = explainer.querySelector(`[data-bar="${index}"]`);
        if (bar) {
          // Leave room for the small gaps between the three coloured segments.
          bar.style.width = `${(value / (endowment * players)) * 96}%`;
        }
      });

      setValue('total-contributions', totalContribution);
      setValue('project-return', projectReturn);
      setValue('individual-share', individualShare);
      setValue('amount-kept', amountKept);
      setValue('your-payoff', payoff);
    };

    inputs.forEach(input => input.addEventListener('input', update));
    update();
  });

  // oTree may render the scripts block before the page markup, depending on the
  // base template in use. Initialise only after the explanatory controls exist.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialiseExplainers, { once: true });
  } else {
    initialiseExplainers();
  }
})();
