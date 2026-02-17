// Jest mock for the manywho global object used by Boomi Flow custom components
const manywho = {
    component: {
        register: jest.fn(),
        getByName: jest.fn(),
    },
    model: {
        getComponent: jest.fn(() => ({
            isVisible: true,
            attributes: {},
        })),
    },
    state: {
        getComponent: jest.fn(() => ({
            loading: false,
        })),
    },
    styling: {
        getClasses: jest.fn(() => []),
    },
    utils: {
        isEqual: jest.fn((a, b) => a === b),
    },
};

global.manywho = manywho;

module.exports = manywho;
