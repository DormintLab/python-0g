import { buildBabyjub, buildEddsa, buildPedersenHash } from 'circomlibjs'

let pedersen = null;

(async () => {
    pedersen = await buildPedersenHash();
})();


function pedersenHashSync(msg) {
    if (!pedersen) throw new Error("Pedersen hash not initialized yet");
    return pedersen.hash(msg);
}


function isReady() {
    return pedersen !== null;
}


module.exports = { pedersenHashSync, isReady };
