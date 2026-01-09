export default class BlockingQueue {
    #items   = [];
    #waiters = [];          // {resolve, reject, min, timer, onTimeout}

    /* Empty queue one-time gate */
    #emptyPromise = null;
    #emptyResolve = null;

    /* Producer: enqueue data */
    enqueue(item, ...restItems) {
        if (restItems.length === 0) {
            this.#items.push(item);
        }
        // If there are additional parameters, batch process all items
        else {
            const items = [item, ...restItems].filter(i => i);
            if (items.length === 0) return;
            this.#items.push(...items);
        }
        // If there's an empty queue gate, release all waiters at once
        if (this.#emptyResolve) {
            this.#emptyResolve();
            this.#emptyResolve = null;
            this.#emptyPromise = null;
        }

        // Wake up all waiting waiters
        this.#wakeWaiters();
    }

    /* Consumer: min items or timeout ms, whichever comes first */
    async dequeue(min = 1, timeout = Infinity, onTimeout = null) {
        // 1. If empty, wait for first data arrival (all calls share the same promise)
        if (this.#items.length === 0) {
            await this.#waitForFirstItem();
        }

        // Immediately satisfied
        if (this.#items.length >= min) {
            return this.#flush();
        }

        // Need to wait
        return new Promise((resolve, reject) => {
            let timer = null;
            const waiter = { resolve, reject, min, onTimeout, timer };

            // Timeout logic
            if (Number.isFinite(timeout)) {
                waiter.timer = setTimeout(() => {
                    this.#removeWaiter(waiter);
                    if (onTimeout) onTimeout(this.#items.length);
                    resolve(this.#flush());
                }, timeout);
            }

            this.#waiters.push(waiter);
        });
    }

    /* Empty queue gate generator */
    #waitForFirstItem() {
        if (!this.#emptyPromise) {
            this.#emptyPromise = new Promise(r => (this.#emptyResolve = r));
        }
        return this.#emptyPromise;
    }

    /* Internal: after each data change, check which waiters are satisfied */
    #wakeWaiters() {
        for (let i = this.#waiters.length - 1; i >= 0; i--) {
            const w = this.#waiters[i];
            if (this.#items.length >= w.min) {
                this.#removeWaiter(w);
                w.resolve(this.#flush());
            }
        }
    }

    #removeWaiter(waiter) {
        const idx = this.#waiters.indexOf(waiter);
        if (idx !== -1) {
            this.#waiters.splice(idx, 1);
            if (waiter.timer) clearTimeout(waiter.timer);
        }
    }

    #flush() {
        const snapshot = [...this.#items];
        this.#items.length = 0;
        return snapshot;
    }

    /* Current cache length (excluding waiters) */
    get length() {
        return this.#items.length;
    }

    /* Clear queue (maintain object reference, don't affect waiters) */
    clear() {
        this.#items.length = 0;
    }
}
